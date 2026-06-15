from django.core.management.base import BaseCommand

from apps.policies.models import Policy

GWIRO_TAGS = ('귀농', '귀촌')


class Command(BaseCommand):
    help = '복지로 정책 중 충북/옥천·귀농귀촌 범위 밖 정책을 비활성화한다 (v2.0.0 현장 피드백)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='비활성화 대상만 출력하고 DB는 변경하지 않음',
        )

    def handle(self, *args, **options):
        qs = Policy.objects.filter(source='복지로', is_active=True)
        targets = [p for p in qs if not _in_scope(p)]

        if options['dry_run']:
            self.stdout.write(f'비활성화 대상: {len(targets)}건 (dry-run, DB 변경 없음)')
            for p in targets:
                self.stdout.write(
                    f'  - [{p.managing_org}] {p.title} '
                    f'(region_codes={p.region_codes}, occupation_tags={p.occupation_tags})'
                )
            return

        ids = [p.id for p in targets]
        updated = Policy.objects.filter(id__in=ids).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'비활성화 완료: {updated}건'))


def _in_scope(policy: Policy) -> bool:
    """충북/옥천 지역 또는 전국(region_codes 없음) 대상이면서, 귀농·귀촌 태그가 있으면 유지 대상."""
    region_in_scope = (
        not policy.region_codes
        or any(code.startswith('43') for code in policy.region_codes)
    )
    has_gwiro_tag = any(tag in GWIRO_TAGS for tag in policy.occupation_tags)
    return region_in_scope and has_gwiro_tag
