import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from .models import House, Room, RoomPoint

TEMP_MEDIA = tempfile.mkdtemp()


def make_jpeg():
    buffer = BytesIO()
    PILImage.new('RGB', (64, 32), 'white').save(buffer, format='JPEG')
    return SimpleUploadedFile('pano.jpg', buffer.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RoomPointTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        house = House.objects.create(owner=self.owner, name='Maison test')
        self.room = Room.objects.create(house=house, title='Salon', image=make_jpeg())
        self.url = reverse('add_room_point', args=[self.room.id])

    def test_owner_can_open_page(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_404(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_info_point_is_saved_without_file(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(self.url, {
            'pitch': '10.5', 'yaw': '-30.2', 'kind': 'info', 'description': 'Prise électrique',
        })
        self.assertRedirects(response, self.url)
        point = RoomPoint.objects.get(room=self.room)
        self.assertEqual(point.kind, 'info')
        self.assertEqual(point.description, 'Prise électrique')
        self.assertAlmostEqual(point.pitch, 10.5)
        self.assertAlmostEqual(point.yaw, -30.2)

    def test_media_point_requires_file(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(self.url, {
            'pitch': '0', 'yaw': '0', 'kind': 'video', 'description': 'Vidéo sans fichier',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'file', 'Veuillez ajouter un fichier pour ce type de point.')
        self.assertFalse(RoomPoint.objects.exists())

    def test_media_point_saved_with_file(self):
        self.client.login(username='owner', password='pass12345')
        sound = SimpleUploadedFile('ambiance.mp3', b'fake-audio', content_type='audio/mpeg')
        self.client.post(self.url, {
            'pitch': '0', 'yaw': '90', 'kind': 'audio', 'description': 'Ambiance', 'file': sound,
        })
        point = RoomPoint.objects.get(room=self.room)
        self.assertEqual(point.kind, 'audio')
        self.assertTrue(point.file.name.startswith('room_points/'))

    def test_points_are_hotspots_on_walkthrough(self):
        RoomPoint.objects.create(room=self.room, pitch=5, yaw=20, kind='info', description='Compteur')
        RoomPoint.objects.create(room=self.room, pitch=-5, yaw=40, kind='audio', description='Ambiance',
                                 file=SimpleUploadedFile('ambiance.mp3', b'fake-audio'))
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('house_walkthrough', args=[self.room.house.id]))
        hotspots = response.context['scenes_json']
        self.assertIn('room-point kind-icon-info', hotspots)
        self.assertIn('room-point kind-icon-audio', hotspots)
        self.assertIn('"URL": "/media/room_points/', hotspots)

    def test_link_point_saved_with_url(self):
        self.client.login(username='owner', password='pass12345')
        self.client.post(self.url, {
            'pitch': '0', 'yaw': '0', 'kind': 'link', 'description': 'Plan du quartier',
            'url': 'https://example.com/plan',
        })
        point = RoomPoint.objects.get(room=self.room)
        self.assertEqual(point.kind, 'link')
        self.assertEqual(point.url, 'https://example.com/plan')
        self.assertFalse(point.file)

    def test_link_point_requires_url(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(self.url, {
            'pitch': '0', 'yaw': '0', 'kind': 'link', 'description': 'Lien vide',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'url', 'Veuillez indiquer le lien à ouvrir.')
        self.assertFalse(RoomPoint.objects.exists())

    def test_link_point_hotspot_opens_its_url(self):
        RoomPoint.objects.create(room=self.room, pitch=0, yaw=0, kind='link', description='Plan',
                                 url='https://example.com/plan')
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('house_walkthrough', args=[self.room.house.id]))
        hotspots = response.context['scenes_json']
        self.assertIn('room-point kind-icon-link', hotspots)
        self.assertIn('"URL": "https://example.com/plan"', hotspots)

    def test_owner_can_edit_point(self):
        point = RoomPoint.objects.create(room=self.room, pitch=5, yaw=20, kind='info', description='Ancien texte')
        self.client.login(username='owner', password='pass12345')
        url = reverse('edit_room_point', args=[point.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modifier le point')
        self.client.post(url, {
            'pitch': '5', 'yaw': '20', 'kind': 'link', 'description': 'Nouveau texte', 'url': 'https://example.com',
        })
        point.refresh_from_db()
        self.assertEqual(point.description, 'Nouveau texte')
        self.assertEqual(point.kind, 'link')
        self.assertEqual(point.url, 'https://example.com')

    def test_other_user_cannot_edit_point(self):
        point = RoomPoint.objects.create(room=self.room, pitch=5, yaw=20, kind='info', description='Privé')
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('edit_room_point', args=[point.id]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_delete_point(self):
        point = RoomPoint.objects.create(room=self.room, pitch=5, yaw=20, kind='info', description='À supprimer')
        self.client.login(username='owner', password='pass12345')
        url = reverse('delete_room_point', args=[point.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, self.url)
        self.assertFalse(RoomPoint.objects.filter(id=point.id).exists())

    def test_other_user_cannot_delete_point(self):
        point = RoomPoint.objects.create(room=self.room, pitch=5, yaw=20, kind='info', description='Privé')
        self.client.login(username='other', password='pass12345')
        response = self.client.post(reverse('delete_room_point', args=[point.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(RoomPoint.objects.filter(id=point.id).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class InspUploadTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('insp_owner', password='pass12345')
        self.house = House.objects.create(owner=self.owner, name='Maison insp')
        self.client.login(username='insp_owner', password='pass12345')
        self.url = reverse('add_room', args=[self.house.id])

    def test_insp_photo_is_accepted_and_saved_as_jpg(self):
        insp = SimpleUploadedFile('pano.insp', make_jpeg().read(), content_type='application/octet-stream')
        response = self.client.post(self.url, {'title': 'Salon', 'image': insp})
        self.assertRedirects(response, reverse('house_detail', args=[self.house.id]))
        room = Room.objects.get(house=self.house)
        self.assertTrue(room.image.name.endswith('.jpg'))

    def test_non_image_file_is_still_refused(self):
        text = SimpleUploadedFile('notes.txt', b'pas une image', content_type='text/plain')
        response = self.client.post(self.url, {'title': 'Salon', 'image': text})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Room.objects.exists())
