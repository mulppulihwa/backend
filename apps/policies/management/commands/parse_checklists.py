import time

from django.core.management.base import BaseCommand

from apps.policies.models import ChecklistItem, Policy
from lib.exceptions import PolicyParseError
from lib.parsing.checklist_parser import parse_checklist


class Command(BaseCommand):
    help = '정책 공고문에서 준비물 체크리스트를 AI로 파싱해 저장합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--policy-id', type=int,
            help='특정 정책 ID만 처리',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='이미 체크리스트가 있는 정책도 재파싱',
        )

    def handle(self, *args, **options):
        qs = Policy.objects.filter(is_active=True).exclude(raw_text='')

        if options['policy_id']:
            qs = qs.filter(pk=options['policy_id'])

        if not options['force']:
            parsed_ids = ChecklistItem.objects.values_list('policy_id', flat=True).distinct()
            qs = qs.exclude(pk__in=parsed_ids)

        total = qs.count()
        if total == 0:
            self.stdout.write('처리할 정책이 없습니다.')
            return

        self.stdout.write(f'{total}개 정책 파싱 시작...')
        success = error = skipped = 0

        for policy in qs.iterator():
            try:
                items = parse_checklist(policy.title, policy.raw_text)
            except PolicyParseError as e:
                self.stderr.write(f'[ERROR] {policy.title} (id={policy.pk}): {e}')
                error += 1
                time.sleep(1)
                continue

            if not items:
                self.stdout.write(f'[SKIP]  {policy.title} — 준비물 없음')
                skipped += 1
                continue

            ChecklistItem.objects.filter(policy=policy).delete()
            ChecklistItem.objects.bulk_create([
                ChecklistItem(policy=policy, order=item['order'], label=item['label'])
                for item in items
            ])
            self.stdout.write(f'[OK]    {policy.title} — {len(items)}개')
            success += 1
            time.sleep(0.5)  # rate limit 방지

        self.stdout.write(
            f'\n완료: 성공 {success} / 준비물없음 {skipped} / 오류 {error} / 전체 {total}'
        )
