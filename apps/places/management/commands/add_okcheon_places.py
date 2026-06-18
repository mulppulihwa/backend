from django.core.management.base import BaseCommand

from apps.places.models import LocalPlace
from lib.services.geocoding import geocode_address

PLACES = [
    # (name, address, phone)
    ('옥천군청',                '충청북도 옥천군 옥천읍 중앙로 99',                     '043-730-3114'),
    ('옥천군의회',              '충북 옥천군 옥천읍 중앙로 99',                          '043-733-7001'),
    ('옥천 귀농귀촌 상담센터',  '충북 옥천군 옥천읍 중앙로 126',                        '043-730-3188'),
    ('옥천군 농업기술센터',     '충북 옥천군 옥천읍 옥천동이로 234',                    '043-731-2912'),
    ('동이면 행정복지센터',     '충북 옥천군 동이면 평산4길 2',                          '043-730-4504'),
    ('안남면 행정복지센터',     '충북 옥천군 안남면 연주길 46',                          '043-730-4543'),
    ('청성면 행정복지센터',     '충북 옥천군 청성면 산계길 53',                          '043-730-4622'),
    ('청산면 행정복지센터',     '충북 옥천군 청산면 지전1길 29',                         '043-730-4664'),
    ('이원면 행정복지센터',     '충북 옥천군 이원면 신흥1길 14',                         '043-730-4704'),
    ('군서면 행정복지센터',     '충북 옥천군 군서면 성왕로 540',                         '043-730-4746'),
    ('군북면 행정복지센터',     '충북 옥천군 군북면 이백길 8',                           '043-730-4782'),
]


class Command(BaseCommand):
    help = '옥천군 행정 사용처를 추가한다'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='DB 변경 없이 대상만 출력')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created = skipped = 0

        for name, address, phone in PLACES:
            existing = LocalPlace.objects.filter(name=name, category='행정').first()
            if existing:
                if existing.lat is not None:
                    self.stdout.write(f'[SKIP] {name} — 이미 존재 (좌표 있음)')
                    skipped += 1
                    continue
                # 좌표 없는 기존 항목은 좌표만 채움
                coords = geocode_address(address)
                if coords and not dry_run:
                    existing.lat, existing.lng = coords
                    existing.save(update_fields=['lat', 'lng'])
                    self.stdout.write(self.style.SUCCESS(f'[FIX]  {name} — {coords[0]}, {coords[1]}'))
                else:
                    self.stdout.write(f'[SKIP] {name} — 좌표 변환 실패')
                    skipped += 1
                continue

            coords = geocode_address(address)
            lat, lng = (coords[0], coords[1]) if coords else (None, None)

            if dry_run:
                self.stdout.write(f'[DRY]  {name} | {address} | {lat}, {lng}')
                continue

            LocalPlace.objects.create(
                name=name,
                category='행정',
                address=address,
                phone=phone,
                lat=lat,
                lng=lng,
                is_active=True,
            )
            coord_str = f'{lat}, {lng}' if lat else '좌표 없음'
            self.stdout.write(self.style.SUCCESS(f'[OK]   {name} — {coord_str}'))
            created += 1

        if not dry_run:
            self.stdout.write(f'\n완료: 추가 {created} / 스킵 {skipped}')
