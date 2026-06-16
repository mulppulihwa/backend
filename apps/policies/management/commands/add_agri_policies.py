from datetime import date

from django.core.management.base import BaseCommand

from apps.policies.models import ChecklistItem, Policy

SOURCE = '옥천군 농업기술센터'
SOURCE_URL = 'https://www.oc.go.kr/agri/selectBbsNttList.do?key=1641&bbsNo=139'

POLICIES = [
    {
        'title': '2026년 하반기 귀농 농업창업 및 주택구입 지원사업',
        'summary': '귀농인 대상 농업창업(최대 3억원)·주택구입(최대 7,500만원) 저금리 대출 지원',
        'description': (
            '대출조건: 연 2.0%, 5년 거치 10년 원금 균등 상환\n'
            '신청장소: 읍면 행정복지센터 산업팀\n'
            '문의: 농촌활력과 귀농귀촌팀 043-730-3882\n'
            '※ 사후관리 기간(15년) 동안 영농에 종사하지 않거나 관외 전출 시 자금 회수 및 제재 조치'
        ),
        'qualification_text': '귀농인, 재촌비농업인, 귀농희망자',
        'how_to_apply': '읍면 행정복지센터 산업팀 방문 신청',
        'apply_institution': '읍면 행정복지센터 산업팀',
        'apply_start_date': date(2026, 6, 9),
        'apply_end_date': date(2026, 6, 30),
        'managing_org': '옥천군 농업기술센터 농촌활력과 귀농귀촌팀',
        'benefit_type': '현금지원',
        'amount_text': '농업창업 최대 3억원, 주택구입·신축 최대 7,500만원 (연 2.0%)',
        'occupation_tags': ['귀농', '귀촌'],
        'is_active': True,
        'checklist': [
            '귀농 농업창업 및 주택구입지원사업 신청서(유형별)',
            '귀농 농업창업계획서',
            '교육이수실적 증빙자료',
            '신용조사서(대출가능금액 미기재)',
            '사업자등록사실여부증명서(해당되는 경우 필수)',
            '가족관계증명서',
            '기타 증빙자료(견적서 등)',
        ],
    },
    {
        'title': '귀농인의 집 11호 입주자 모집',
        'summary': '안남면 화학리 귀농인의 집 11호 1가구 입주자 모집 (재공고)',
        'description': (
            '대상지: 귀농인의 집 11호(안남면 화학리) / 1가구\n'
            '재공고 사유: 기한 내 지원자 없음'
        ),
        'qualification_text': (
            '공고일(2026.6.15) 기준 1년 이상 연속하여 농어촌 이외 지역 거주(주민등록 기준), '
            '19세 이상 대한민국 국적자'
        ),
        'how_to_apply': '방문 또는 등기우편 접수 [(29043) 충청북도 옥천군 옥천읍 옥천동이로 234, 옥천군농업기술센터 농촌활력과 귀농귀촌팀]',
        'apply_institution': '옥천군농업기술센터 농촌활력과 귀농귀촌팀',
        'apply_start_date': date(2026, 6, 15),
        'apply_end_date': date(2026, 6, 29),
        'managing_org': '옥천군 농업기술센터 농촌활력과 귀농귀촌팀',
        'benefit_type': '시설',
        'occupation_tags': ['귀농', '귀촌'],
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '2026년 하반기 로컬푸드 생산자 신규 교육',
        'summary': '로컬푸드 사업 참여 희망 신규 농업인 대상 3일 과정 교육 (50명)',
        'description': (
            '교육일자: 2026.7.8(수) ~ 7.10(금) (3일, 16시간)\n'
            '교육장소: 옥천군 농업기술센터 농업인교육관, 로컬푸드직매장 등\n'
            '교육내용: 로컬푸드·친환경·옥천푸드 인증 관련 이론 및 현지견학\n'
            '문의: 로컬푸드팀 043-730-3283'
        ),
        'qualification_text': '옥천군 관내 거주하며 관내 필지를 경작하는 농업경영체 등록 농업인',
        'how_to_apply': '거주지 읍면사무소 방문 신청 (붙임서식 참조)',
        'apply_institution': '거주지 읍면사무소',
        'apply_end_date': date(2026, 6, 24),
        'managing_org': '옥천군 농업기술센터 농촌활력과 로컬푸드팀',
        'benefit_type': '교육',
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '리턴팜·러스틱하우스 입주자 모집',
        'summary': '이원면 리턴팜·러스틱하우스 2가구 입주자 모집',
        'description': (
            '대상지: 이원면 이원로 443-1 / 2가구\n'
            '접수주소: (29043) 충청북도 옥천군 옥천읍 옥천동이로 234, 옥천군농업기술센터 농촌활력과 귀농귀촌팀'
        ),
        'qualification_text': (
            '공고일(2026.6.1) 기준 1년 이상 연속하여 농어촌 이외 지역 거주(주민등록 기준), '
            '19세 이상 대한민국 국적자'
        ),
        'how_to_apply': '방문 또는 등기우편 접수',
        'apply_institution': '옥천군농업기술센터 농촌활력과 귀농귀촌팀',
        'apply_start_date': date(2026, 6, 2),
        'apply_end_date': date(2026, 6, 19),
        'managing_org': '옥천군 농업기술센터 농촌활력과 귀농귀촌팀',
        'benefit_type': '시설',
        'occupation_tags': ['귀농', '귀촌'],
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '2026년 과수 무병묘 모수포 조성 지원',
        'summary': '5대 과수 무병 모수 보존·유지 및 무병묘 생산 시설 지원 (최대 100만원)',
        'description': (
            '사업내용: 비가림시설 등 신규 설치 또는 기존 시설 개·보수 지원\n'
            '지원 개소: 1개소 내외\n'
            '신청방법: e나라도움 공모 신청'
        ),
        'qualification_text': '5과종(사과·배·복숭아·포도·감귤) 모수를 보유하거나 보유하고자 하는 종자업체 및 농업단체',
        'how_to_apply': 'e나라도움(gosims.go.kr) 공모 신청 접수',
        'apply_institution': 'e나라도움',
        'apply_start_date': date(2026, 5, 27),
        'apply_end_date': date(2026, 6, 30),
        'managing_org': '옥천군 농업기술센터',
        'benefit_type': '현금지원',
        'amount_text': '최대 100만원',
        'is_active': True,
        'checklist': [
            '사업신청서',
            '계획서',
            '증빙서류',
        ],
    },
    {
        'title': '2027년 유기질비료 지원사업',
        'summary': '농업경영체 등록 농업인 대상 유기질비료·부숙유기질비료 구입비 일부 지원',
        'description': (
            '대상비료: 유기질비료(혼합유박·혼합유기질·유기복합비료), 부숙유기질비료(가축분퇴비·퇴비)\n'
            '온라인 신청: 2026.6.1~6.10 [농업e지 www.nongupez.go.kr]\n'
            '대면 신청: 2026.6.11~7.10 [농지소재지 읍면 행정복지센터 산업팀]'
        ),
        'qualification_text': '농업경영정보를 등록한 농업경영체로서 유기질비료를 농산물 생산에 사용하는 자',
        'how_to_apply': '온라인: 농업e지(www.nongupez.go.kr) / 대면: 농지소재지 읍면 행정복지센터 산업팀 방문',
        'apply_institution': '농업e지 또는 읍면 행정복지센터 산업팀',
        'apply_end_date': date(2026, 7, 10),
        'managing_org': '옥천군 농업기술센터',
        'benefit_type': '현금지원',
        'is_active': True,
        'checklist': [],
    },
    {
        'title': '2026년 치유농업시설 운영자 기초과정 교육',
        'summary': '치유농장 운영 희망 농업인 대상 기초과정 교육 (30명, 2026년 6~9월)',
        'description': (
            '교육기간: 2026.6~9월 (14회, 101시간)\n'
            '교육장소: 충북농업기술원 치유농업센터, 재택(온라인), 현장실습장\n'
            '교육방법: 대면·비대면 병행 (강의, 현장실습, 온라인)\n'
            '교육내용: 치유농업이해, 시설 준비·운영, 프로그램 운영 등\n'
            '문의: 농촌자원팀 043-730-4914, 043-730-4932 / 주관: 충북농업기술원'
        ),
        'qualification_text': '치유농장을 운영하거나 희망하는 농업인, PC·노트북·핸드폰 등 온라인 교육 가능한 자',
        'how_to_apply': '옥천농업기술센터 기술지원과 농촌자원팀 방문 접수',
        'apply_institution': '옥천농업기술센터 기술지원과 농촌자원팀',
        'apply_end_date': date(2026, 5, 27),
        'managing_org': '옥천군 농업기술센터 기술지원과 농촌자원팀',
        'benefit_type': '교육',
        'is_active': False,  # 접수 마감
        'checklist': [],
    },
    {
        'title': '2026년 옥천로컬푸드 잡초관리 피복재 지원사업',
        'summary': '옥천푸드·친환경 인증 농업인 대상 잡초관리 피복재 구입비 지원 (보조 80%)',
        'description': (
            '지원단가: 제초매트 330원/㎡, 흑색부직포 360원/㎡, 제초용차광막 690원/㎡\n'
            '지원비율: 보조 80%, 자담 20%\n'
            '신청장소: 사업장 소재지 읍면 행정복지센터 산업팀'
        ),
        'qualification_text': (
            '농업경영정보 등록 농업인 + 로컬푸드 생산자 신규교육 이수자 + '
            '옥천푸드 또는 친환경 인증 취득한 관내 거주 농업인 (모두 충족)'
        ),
        'how_to_apply': '사업장 소재지 읍면 행정복지센터 산업팀 방문 신청',
        'apply_institution': '읍면 행정복지센터 산업팀',
        'apply_end_date': date(2026, 6, 12),
        'managing_org': '옥천군 농업기술센터',
        'benefit_type': '현금지원',
        'amount_text': '보조 80%',
        'is_active': False,  # 접수 마감
        'checklist': [],
    },
    {
        'title': '2026년 6월 로컬푸드 요리교실',
        'summary': '지역 친환경 로컬푸드 식재료 활용 요리교실 (무료, 20명, 2026.6.19)',
        'description': (
            '일시: 2026.6.19(금) 10:00~12:00\n'
            '장소: 옥천군농업기술센터 3층 가공교육장 (옥천읍 옥천동이로 234)\n'
            '메뉴: 닭가슴살 타코, 감자수프\n'
            '참가비: 무료\n'
            '제한: 연간 3회까지, 당일 미참석 시 1년간 참여 제한\n'
            '문의: 옥천로컬푸드직매장 043-733-6291'
        ),
        'qualification_text': '직매장 회원 및 지역 주민, 20명 내외 (선착순)',
        'how_to_apply': 'QR코드로 사전 신청 (선착순 마감, 대리 신청 불가)',
        'apply_institution': '옥천로컬푸드직매장',
        'apply_end_date': date(2026, 6, 12),
        'managing_org': '옥천군 농업기술센터',
        'benefit_type': '교육',
        'is_active': False,  # 신청 마감
        'checklist': [],
    },
]


class Command(BaseCommand):
    help = '옥천군 농업기술센터 정책을 추가한다'

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

            policy = Policy.objects.create(
                source=SOURCE,
                source_url=SOURCE_URL,
                apply_url=SOURCE_URL,
                **{k: v for k, v in data.items()
                   if k not in ('apply_start_date', 'apply_end_date',
                                'occupation_tags', 'checklist')},
                apply_start_date=data.get('apply_start_date'),
                apply_end_date=data.get('apply_end_date'),
                occupation_tags=data.get('occupation_tags', []),
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
