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
