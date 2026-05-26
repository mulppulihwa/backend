from django.core.management.base import BaseCommand

from lib.sync.adapters.bokjiro_sync import sync_bokjiro


class Command(BaseCommand):
    help = '복지로 API에서 정책 데이터를 동기화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-page',
            type=int,
            default=100,
            help='페이지당 항목 수 (기본값: 100)',
        )
        parser.add_argument(
            '--max-items',
            type=int,
            default=None,
            help='처리할 최대 항목 수 (테스트용)',
        )

    def handle(self, *args, **options):
        self.stdout.write('복지로 동기화 시작...')
        result = sync_bokjiro(per_page=options['per_page'], max_items=options['max_items'])
        self.stdout.write(self.style.SUCCESS(
            f"완료 — 저장: {result['saved']}개 | "
            f"스킵: {result['skipped']}개 | "
            f"낮은신뢰도: {result['low_confidence']}개"
        ))
