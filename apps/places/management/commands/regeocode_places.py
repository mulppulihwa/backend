from django.core.management.base import BaseCommand

from lib.services.geocoding import geocode_address

from apps.places.models import LocalPlace


class Command(BaseCommand):
    help = 'lat/lng가 비어 있는 사용처를 주소 기반으로 다시 지오코딩한다'

    def handle(self, *args, **options):
        qs = LocalPlace.objects.filter(lat__isnull=True).exclude(address='')
        total = qs.count()
        if total == 0:
            self.stdout.write('좌표 없는 사용처가 없습니다.')
            return

        success = fail = 0
        for place in qs:
            coords = geocode_address(place.address)
            if coords is None:
                self.stderr.write(f'[FAIL] {place.name} (id={place.id}) — {place.address}')
                fail += 1
                continue
            place.lat, place.lng = coords
            place.save(update_fields=['lat', 'lng'])
            self.stdout.write(self.style.SUCCESS(f'[OK]   {place.name} (id={place.id}) — {coords}'))
            success += 1

        self.stdout.write(f'\n완료: 성공 {success} / 실패 {fail} / 전체 {total}')
