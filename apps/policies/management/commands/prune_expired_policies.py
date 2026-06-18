from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.policies.models import Policy


class Command(BaseCommand):
    help = '마감일이 지난 정책을 DB에서 삭제한다 (UserPolicy · ChecklistItem CASCADE 삭제 포함)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='삭제 대상만 출력하고 DB는 변경하지 않음',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        qs = Policy.objects.filter(apply_end_date__lt=today)

        if options['dry_run']:
            count = qs.count()
            self.stdout.write(f'삭제 대상: {count}건 (dry-run, DB 변경 없음)')
            for p in qs.order_by('apply_end_date'):
                self.stdout.write(f'  - [{p.apply_end_date}] {p.title} (source={p.source})')
            return

        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f'삭제 완료: {count}건 (UserPolicy · ChecklistItem 포함)'))
