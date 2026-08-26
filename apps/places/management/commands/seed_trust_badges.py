from django.core.management.base import BaseCommand

from lib.services.geocoding import geocode_address

from apps.places.models import LocalPlace

# 옥천군 상담센터 / 옥천신문 추천 마크 수기 반영 (2026-08-26)
BADGES = [
    # (place name, badge field)
    ('아세아농기계 옥천대리점', 'counseling_center_recommended'),
    ('옥천군주민정보화교육장', 'counseling_center_recommended'),
    ('맥우직매장', 'counseling_center_recommended'),
    ('배바우손두부', 'okcheon_news_recommended'),
    ('옥천체육센터', 'okcheon_news_recommended'),
]

NEW_PLACES = [
    {
        'name': '맥우직매장',
        'category': '음식점',
        'address': '충청북도 옥천군 군서면 성왕로 975',
    },
]


class Command(BaseCommand):
    help = '옥천군 상담센터/옥천신문 추천 마크를 수기로 반영한다 (관리자 큐레이션)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='적용될 내용만 출력하고 DB는 변경하지 않음',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        for data in NEW_PLACES:
            if LocalPlace.objects.filter(name=data['name']).exists():
                self.stdout.write(f'[SKIP] {data["name"]} — 이미 존재함')
                continue

            if dry_run:
                self.stdout.write(f'[DRY]  신규 등록: {data["name"]} ({data["category"]}) — {data["address"]}')
                continue

            coords = geocode_address(data['address'])
            lat, lng = coords if coords else (None, None)
            place = LocalPlace.objects.create(
                name=data['name'], category=data['category'], address=data['address'],
                lat=lat, lng=lng,
            )
            geo_status = f'{lat}, {lng}' if lat else '좌표 변환 실패 — 수동 확인 필요'
            self.stdout.write(self.style.SUCCESS(f'[OK]   신규 등록: {place.name} (id={place.id}) — {geo_status}'))

        for name, field in BADGES:
            try:
                place = LocalPlace.objects.get(name=name)
            except LocalPlace.DoesNotExist:
                self.stderr.write(f'[SKIP] {name} — 사용처를 찾을 수 없음')
                continue
            except LocalPlace.MultipleObjectsReturned:
                self.stderr.write(f'[SKIP] {name} — 동명 사용처가 여러 개라 수동 확인 필요')
                continue

            if getattr(place, field):
                self.stdout.write(f'[SKIP] {name} — 이미 {field}=True')
                continue

            if dry_run:
                self.stdout.write(f'[DRY]  {name} (id={place.id}) — {field}=True')
                continue

            setattr(place, field, True)
            place.save(update_fields=[field])
            self.stdout.write(self.style.SUCCESS(f'[OK]   {name} (id={place.id}) — {field}=True'))
