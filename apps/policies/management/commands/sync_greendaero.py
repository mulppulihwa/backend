from django.core.management.base import BaseCommand

from lib.sync.adapters.greendaero_sync import sync_greendaero


class Command(BaseCommand):
    help = '그린대로(greendaero.go.kr)에서 귀농·농업 지원사업 정책을 동기화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-items',
            type=int,
            default=None,
            help='처리할 최대 항목 수 (테스트용)',
        )

    def handle(self, *args, **options):
        self.stdout.write('그린대로 동기화 시작...')
        result = sync_greendaero(max_items=options['max_items'])
        self.stdout.write(self.style.SUCCESS(
            f"완료 — 저장: {result['saved']}개 | "
            f"스킵: {result['skipped']}개 | "
            f"낮은신뢰도: {result['low_confidence']}개"
        ))
