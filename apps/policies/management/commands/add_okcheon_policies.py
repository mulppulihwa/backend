from datetime import date

from django.core.management.base import BaseCommand

from apps.policies.models import ChecklistItem, Policy

SOURCE = '옥천군청'
SOURCE_URL = 'https://www.oc.go.kr'

POLICIES = [
    {
        'title': '2026년 충북행복결혼공제 모집',
        'summary': '충북 거주 19~39세 미혼 청년 대상 결혼공제 — 매월 적립 후 결혼 시 지자체 매칭금액 지급',
        'description': (
            '모집인원: 19명 (예산액 범위 내 변경 가능)\n'
            '지원기간: 5년 만기\n'
            '지원내용: 매월 일정액 납입 시 지자체 등에서 매칭 적립, 기간 내 결혼한 경우 만기목돈 지급\n'
            '문의: 옥천군청 성장정책과 인구정책팀 043-730-3783'
        ),
        'qualification_text': (
            '주민등록상 충청북도 거주, 19세 이상 39세 이하 미혼 청년, '
            '도내 중소(견)기업 근로자·농업인·소상공인 (구분 없이 신청 가능)'
        ),
        'how_to_apply': '증빙서류 갖추어 방문 신청 (문의: 옥천군청 성장정책과 인구정책팀 043-730-3783)',
        'apply_institution': '옥천군청 성장정책과 인구정책팀',
        'apply_start_date': date(2026, 1, 14),
        'apply_end_date': None,
        'managing_org': '옥천군청 성장정책과 인구정책팀',
        'benefit_type': '현금지원',
        'amount_text': '5년 만기 매칭적립금 (월 납입액 + 지자체 매칭)',
        'min_age': 19,
        'max_age': 39,
        'occupation_tags': [],
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '옥천군 농어촌 기본소득',
        'summary': '옥천군 주민 대상 매월 15만원 기본소득 지급 (향수OK카드)',
        'description': (
            '지급일: 매월 27일 경\n'
            '사용방법(읍 주민): 지급일로부터 90일 이내, 읍·면지역 향수OK카드 가맹점 사용\n'
            '사용방법(면 주민): 지급일로부터 180일 이내, 면지역 향수OK카드 가맹점 사용\n'
            '절차: 신청 → 자격 확인 → 지급 대상자 결정 → 지급\n'
            '※ 신규 전입자는 90일 실거주 확인 후 소급 지급'
        ),
        'qualification_text': (
            '신청일 직전 30일 이상 옥천군에 주민등록을 두고 주 3일 이상 거주 '
            '(신규 전입자는 90일 실거주 확인 후 소급 지급)'
        ),
        'how_to_apply': '주소지 관할 읍/면 행정복지센터 본인 방문 신청 (온라인 불가, 최초 1회)',
        'apply_institution': '읍/면 행정복지센터',
        'apply_start_date': None,
        'apply_end_date': None,
        'managing_org': '옥천군청',
        'benefit_type': '현금지원',
        'amount_text': '매월 15만원 (향수OK카드)',
        'occupation_tags': [],
        'is_active': True,
        'checklist': [
            '[본인신청] 신청서',
            '[본인신청] 신분증',
            '[본인신청] 향수OK카드',
            '[대리신청] 위임장',
            '[대리신청] 대리인 신분증',
            '[대리신청] 관계 증명서',
        ],
    },
    {
        'title': '2026년 청년 부동산 중개보수 및 이사비 지원',
        'summary': '옥천군 전입 19~39세 청년 가구 대상 중개보수·이사비 최대 50만원 지원 (생애 1회)',
        'description': (
            '지급방식: 청년 본인 계좌로 현금 지급\n'
            '주택요건: 임차보증금 5천만원 이하 및 월세 50만원 이하\n'
            '※ 2024.1.1 이후 옥천군 전입 또는 옥천군 내 이사 후 전입신고 완료한 경우'
        ),
        'qualification_text': (
            '2024.1.1 이후 옥천군 전입 및 전입신고 완료, '
            '19세 이상 39세 이하 (1986.1.1~2006.12.31 출생), '
            '기준중위소득 180% 이하, 무주택자 (세대주·세대원 모두), '
            '임차보증금 5천만원 이하 및 월세 50만원 이하 주택'
        ),
        'how_to_apply': '증빙서류 갖추어 방문 신청',
        'apply_institution': '옥천군청',
        'apply_start_date': date(2026, 1, 16),
        'apply_end_date': None,
        'managing_org': '옥천군청',
        'benefit_type': '현금지원',
        'amount_text': '최대 50만원 (중개보수료 30만원 + 이사비 20만원, 생애 1회)',
        'min_age': 19,
        'max_age': 39,
        'occupation_tags': [],
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '2026년 청년농업인 영농정착지원사업 2차',
        'summary': '18세 이상 40세 미만 청년농업인 대상 영농정착지원금 월 최대 110만원·창업자금 최대 5억원 지원',
        'description': (
            '영농창업자금: 금리 연 1.5%, 5년 거치 20년 원금 균등분할 상환\n'
            '문의: 옥천군청 농업정책과 농정지원팀 043-730-3246\n'
            '※ 방문 수기 접수 불가 (농업e지 온라인 신청만 가능)\n'
            '※ 신청 시 시군구 반드시 선택'
        ),
        'qualification_text': (
            '18세 이상 40세 미만 예비(청년)농업인 (1986~2008년 출생), '
            '독립경영 3년 이하 농업인 (2023.1.1 이후 농업경영체 경영주 등록자)'
        ),
        'how_to_apply': '농업e지(uni.nongupez.go.kr) 로그인 후 사업 선택·신청 (온라인 전용)',
        'apply_institution': '농업e지 (uni.nongupez.go.kr)',
        'apply_url': 'https://uni.nongupez.go.kr',
        'apply_start_date': date(2026, 6, 1),
        'apply_end_date': date(2026, 7, 10),
        'managing_org': '옥천군청 농업정책과 농정지원팀',
        'benefit_type': '현금지원',
        'amount_text': '영농정착지원금 월 최대 110만원 (최장 3년), 영농창업자금 최대 5억원',
        'min_age': 18,
        'max_age': 39,
        'occupation_tags': ['귀농'],
        'is_active': True,
        'checklist': [
            '신청서 (농업e지 시스템 입력)',
            '영농계획서 (시스템 첨부)',
            '기타 증빙자료 (시스템 첨부)',
        ],
    },
]


class Command(BaseCommand):
    help = '옥천군청 정책을 추가한다'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='DB 변경 없이 대상만 출력')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created = skipped = 0

        for data in POLICIES:
            checklist = data.pop('checklist')
            title = data['title']

            if Policy.objects.filter(title=title, source=SOURCE).exists():
                self.stdout.write(f'[SKIP] {title}')
                skipped += 1
                data['checklist'] = checklist
                continue

            if dry_run:
                self.stdout.write(f'[DRY]  {title} (체크리스트 {len(checklist)}개)')
                data['checklist'] = checklist
                continue

            exclude_keys = {'apply_start_date', 'apply_end_date', 'occupation_tags',
                            'min_age', 'max_age', 'apply_url'}
            fields = {k: v for k, v in data.items() if k not in exclude_keys}

            policy = Policy.objects.create(
                source=SOURCE,
                source_url=SOURCE_URL,
                apply_url=data.get('apply_url', SOURCE_URL),
                apply_start_date=data.get('apply_start_date'),
                apply_end_date=data.get('apply_end_date'),
                occupation_tags=data.get('occupation_tags', []),
                min_age=data.get('min_age', 0),
                max_age=data.get('max_age', 130),
                **fields,
            )

            if checklist:
                ChecklistItem.objects.bulk_create([
                    ChecklistItem(policy=policy, order=i, label=label)
                    for i, label in enumerate(checklist)
                ])

            status = '활성' if policy.is_active else '비활성(마감)'
            self.stdout.write(self.style.SUCCESS(
                f'[OK]   {title} [{status}] (체크리스트 {len(checklist)}개)'
            ))
            data['checklist'] = checklist
            created += 1

        self.stdout.write(f'\n완료: 추가 {created} / 스킵 {skipped}')
