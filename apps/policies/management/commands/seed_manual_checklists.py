from django.core.management.base import BaseCommand

from apps.policies.models import ChecklistItem, Policy

DRAFTS = {
    1444: [
        '신청서 (옥천군청 지정 양식)',
        '신분증 사본',
        '주민등록등본',
        '혼인관계증명서 (미혼 확인용)',
        '재직증명서 또는 사업자등록증 (근로자·소상공인 증빙)',
        '농업경영체등록확인서 (농업인 증빙 시)',
    ],
    1446: [
        '신청서 (옥천군청 지정 양식)',
        '주민등록등본 (전입일 확인용)',
        '임대차계약서 사본',
        '부동산 중개보수 영수증 (현금영수증/세금계산서)',
        '이사비 영수증',
        '통장사본',
        '건강보험 자격득실확인서 (무주택 확인용)',
        '소득금액증명원 (기준중위소득 확인용)',
    ],
}


class Command(BaseCommand):
    help = (
        'qualification_text/how_to_apply 원문이 있는 정책에 한해 초안 체크리스트를 채운다 '
        '(2026-08-26 체크리스트 커버리지 점검 작업 — id 1444, 1446)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='저장할 내용만 출력하고 DB는 변경하지 않음',
        )

    def handle(self, *args, **options):
        for policy_id, labels in DRAFTS.items():
            try:
                policy = Policy.objects.get(pk=policy_id)
            except Policy.DoesNotExist:
                self.stderr.write(f'[SKIP] id={policy_id} 정책을 찾을 수 없음')
                continue

            if options['dry_run']:
                self.stdout.write(f'[DRY] {policy.title} (id={policy_id}) — {len(labels)}개')
                for label in labels:
                    self.stdout.write(f'   - {label}')
                continue

            ChecklistItem.objects.filter(policy=policy).delete()
            ChecklistItem.objects.bulk_create([
                ChecklistItem(policy=policy, order=i, label=label)
                for i, label in enumerate(labels)
            ])
            self.stdout.write(self.style.SUCCESS(f'[OK] {policy.title} (id={policy_id}) — {len(labels)}개 저장'))
