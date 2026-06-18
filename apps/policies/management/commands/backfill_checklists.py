from django.core.management.base import BaseCommand

from apps.policies.models import ChecklistItem, Policy
from lib.sync.adapters.bokjiro_sync import _fetch_checklist_labels
from django.conf import settings
from django.core.cache import cache


class Command(BaseCommand):
    help = '복지로 정책의 구비서류를 serviceDetail API에서 직접 채웁니다 (Claude API 불필요)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='이미 체크리스트가 있는 정책도 재처리')

    def handle(self, *args, **options):
        api_key = getattr(settings, 'BOKJIRO_API_KEY', '')
        if not api_key:
            self.stderr.write('BOKJIRO_API_KEY가 설정되지 않았습니다.')
            return

        qs = Policy.objects.filter(source='복지로', is_active=True).exclude(external_id='')
        if not options['force']:
            has_checklist = ChecklistItem.objects.values_list('policy_id', flat=True).distinct()
            qs = qs.exclude(pk__in=has_checklist)

        total = qs.count()
        if total == 0:
            self.stdout.write('처리할 정책이 없습니다.')
            return

        self.stdout.write(f'{total}개 정책 처리 시작...')
        success = empty = error = 0

        for policy in qs.iterator():
            labels = _fetch_checklist_labels(policy.external_id, api_key)
            if labels is None:
                error += 1
                continue
            if not labels:
                self.stdout.write(f'[SKIP]  {policy.title} — 구비서류 없음')
                empty += 1
                continue

            ChecklistItem.objects.filter(policy=policy).delete()
            ChecklistItem.objects.bulk_create([
                ChecklistItem(policy=policy, order=i, label=label)
                for i, label in enumerate(labels)
            ])
            cache.delete(f'checklist:{policy.pk}')
            self.stdout.write(f'[OK]    {policy.title} — {len(labels)}개')
            success += 1

        self.stdout.write(f'\n완료: 성공 {success} / 구비서류없음 {empty} / 오류 {error} / 전체 {total}')
