-- ============================================================
-- socialventure ERD Schema
-- DB: PostgreSQL (Supabase)
-- Generated from Django models as of 2026-05-27
-- ============================================================

-- ------------------------------------------------------------
-- regions
-- ------------------------------------------------------------
CREATE TABLE regions (
    code        VARCHAR(10)  PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,
    parent_code VARCHAR(10)  DEFAULT NULL
);

COMMENT ON TABLE  regions              IS '행정구역 코드 (시도/시군구). 예: 43=충청북도, 43720=옥천군';
COMMENT ON COLUMN regions.code        IS '행정구역 코드 (예: 43720)';
COMMENT ON COLUMN regions.parent_code IS '상위 행정구역 코드 (시군구→시도). recursive CTE 지역 계층 조회에 사용';


-- ------------------------------------------------------------
-- users  (Django AbstractUser 확장)
-- ------------------------------------------------------------
CREATE TABLE users (
    id                 BIGSERIAL    PRIMARY KEY,
    kakao_id           TEXT         NOT NULL UNIQUE,
    password           VARCHAR(128) NOT NULL,
    nickname           TEXT         NOT NULL DEFAULT '',
    phone              TEXT         NOT NULL DEFAULT '',
    profile_completed  BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    is_staff           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_superuser       BOOLEAN      NOT NULL DEFAULT FALSE,
    date_joined        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login         TIMESTAMPTZ  DEFAULT NULL,
    email              VARCHAR(254) NOT NULL DEFAULT '',
    first_name         VARCHAR(150) NOT NULL DEFAULT '',
    last_name          VARCHAR(150) NOT NULL DEFAULT ''
);

COMMENT ON TABLE  users                   IS '인증 정보 (카카오 OAuth + JWT). 정책 매칭 기준은 user_profiles에 분리';
COMMENT ON COLUMN users.kakao_id          IS 'JWT USERNAME_FIELD. 카카오 사용자 고유 ID';
COMMENT ON COLUMN users.profile_completed IS '온보딩 완료 여부. False이면 프론트에서 온보딩 화면으로 이동';
COMMENT ON COLUMN users.phone             IS '카카오 알림톡 발송용 (v1.5)';


-- ------------------------------------------------------------
-- user_profiles  (정책 매칭 기준 데이터)
-- ------------------------------------------------------------
CREATE TABLE user_profiles (
    id                   BIGSERIAL    PRIMARY KEY,
    user_id              BIGINT       NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- 기본 정보
    region_code          TEXT         NOT NULL DEFAULT '',
    birth_date           DATE         DEFAULT NULL,
    gender               VARCHAR(5)   NOT NULL DEFAULT '',   -- '남' | '여'

    -- 귀농/귀촌 상태
    occupation_tags      TEXT[]       NOT NULL DEFAULT '{}',
    move_in_date         DATE         DEFAULT NULL,

    -- 경제 상태
    household_type       VARCHAR(10)  NOT NULL DEFAULT '',   -- '독거' | '부부' | '기타'
    income_level         VARCHAR(10)  NOT NULL DEFAULT '',   -- '기초수급' | '차상위' | '일반'
    non_farm_income      INTEGER      DEFAULT NULL,          -- 농업외 소득 (만원 단위)
    marital_status       VARCHAR(5)   NOT NULL DEFAULT '',   -- '미혼' | '기혼'

    -- 농업 자격
    is_farm_registered   BOOLEAN      DEFAULT NULL,
    farm_registered_date DATE         DEFAULT NULL,
    education_hours      SMALLINT     NOT NULL DEFAULT 0,

    -- 복지로 API 매칭용
    is_disabled          BOOLEAN      DEFAULT NULL           -- NULL=무관, TRUE=장애인
);

COMMENT ON TABLE  user_profiles                   IS '정책 매칭 기준 데이터. users와 1:1. age/years_since_move는 앱 레이어 property로 계산';
COMMENT ON COLUMN user_profiles.region_code       IS 'regions.code 참조 (FK 없음 — 유연성 확보). 지역 계층 조회는 get_ancestor_codes() 사용';
COMMENT ON COLUMN user_profiles.occupation_tags   IS '가능한 값: 귀농, 귀촌, 노인, 여성농업인';
COMMENT ON COLUMN user_profiles.move_in_date      IS '"전입 후 N년 이내" 조건 계산용. years_since_move property로 사용';
COMMENT ON COLUMN user_profiles.non_farm_income   IS '농업인 공익수당 농업외 소득 3700만원 미만 조건 대응';
COMMENT ON COLUMN user_profiles.is_farm_registered IS '농업경영체 등록 여부';
COMMENT ON COLUMN user_profiles.farm_registered_date IS '농업경영체 등록일. "1년 이상 등록" 조건 계산용';
COMMENT ON COLUMN user_profiles.education_hours   IS '귀농교육 이수 시간. 8시간/100시간 조건 대응';
COMMENT ON COLUMN user_profiles.is_disabled       IS '장애 여부. 노인 장애 복지 정책 매칭용';


-- ------------------------------------------------------------
-- policies
-- ------------------------------------------------------------
CREATE TABLE policies (
    id               BIGSERIAL    PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    summary          TEXT         NOT NULL,
    description      TEXT         NOT NULL DEFAULT '',
    benefit_type     VARCHAR(20)  NOT NULL DEFAULT '',  -- '현금지원'|'교육'|'컨설팅'|'시설'|'세금감면'|'현물'|'기타'
    amount           INTEGER      DEFAULT NULL,
    amount_text      VARCHAR(100) NOT NULL DEFAULT '',
    source           VARCHAR(20)  NOT NULL DEFAULT '수동입력',  -- '복지로'|'수동입력'|'귀농센터'

    -- 1차 SQL 필터 조건
    min_age          SMALLINT     NOT NULL DEFAULT 0,
    max_age          SMALLINT     NOT NULL DEFAULT 130,
    gender           VARCHAR(10)  NOT NULL DEFAULT 'all',
    region_codes     TEXT[]       NOT NULL DEFAULT '{}',
    occupation_tags  TEXT[]       NOT NULL DEFAULT '{}',
    household_type   TEXT[]       NOT NULL DEFAULT '{}',
    move_status      TEXT[]       NOT NULL DEFAULT '{}',
    income_level     TEXT[]       NOT NULL DEFAULT '{}',
    disability_required BOOLEAN   DEFAULT NULL,          -- NULL=무관, TRUE=장애인만

    -- 복합 조건 트리 (단순 태그로 표현 불가한 경우에만)
    condition_tree   JSONB        DEFAULT NULL,

    -- AI 파싱용 공고문 원문
    raw_text         TEXT         NOT NULL DEFAULT '',

    -- 신청 정보
    apply_start_date DATE         DEFAULT NULL,
    apply_end_date   DATE         DEFAULT NULL,
    apply_url        VARCHAR(200) NOT NULL DEFAULT '',
    managing_org     VARCHAR(100) NOT NULL DEFAULT '',
    source_url       VARCHAR(200) NOT NULL DEFAULT '',
    external_id      VARCHAR(100) NOT NULL DEFAULT '',
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  policies                    IS '정책 목록. SQL 1차 필터 + condition_tree 2차 평가로 매칭';
COMMENT ON COLUMN policies.region_codes       IS '빈 배열 = 전국 대상. overlap 연산으로 지역 계층 코드와 비교';
COMMENT ON COLUMN policies.occupation_tags    IS '빈 배열 = 전체 대상. 가능한 값: 귀농, 귀촌, 노인, 여성농업인';
COMMENT ON COLUMN policies.income_level       IS '빈 배열 = 전체 소득 대상. 가능한 값: 기초수급, 차상위, 일반';
COMMENT ON COLUMN policies.household_type     IS '빈 배열 = 전체. 가능한 값: 독거, 부부, 기타';
COMMENT ON COLUMN policies.disability_required IS 'NULL=무관, TRUE=장애인만';
COMMENT ON COLUMN policies.condition_tree     IS 'AND/OR/NOT/LEAF 노드로 구성된 복합 조건 트리. lib/condition_tree.py로 평가';
COMMENT ON COLUMN policies.raw_text           IS '공고문 원문. Claude API 파싱(parse_policy) 입력용';
COMMENT ON COLUMN policies.external_id        IS '복지로 서비스ID 등 외부 출처 식별자. update_or_create 중복 방지 키';
COMMENT ON COLUMN policies.source             IS '복지로|수동입력|귀농센터';


-- ------------------------------------------------------------
-- user_policies  (사용자 정책 저장 상태)
-- ------------------------------------------------------------
CREATE TABLE user_policies (
    id             BIGSERIAL    PRIMARY KEY,
    profile_id     BIGINT       NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    policy_id      BIGINT       NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    status         VARCHAR(10)  NOT NULL DEFAULT '신청예정',  -- '신청예정'|'신청완료'|'관심없음'
    d7_alerted_at  TIMESTAMPTZ  DEFAULT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE (profile_id, policy_id)
);

COMMENT ON TABLE  user_policies               IS '사용자가 저장한 정책과 신청 상태';
COMMENT ON COLUMN user_policies.status        IS '신청예정(기본)|신청완료|관심없음';
COMMENT ON COLUMN user_policies.d7_alerted_at IS '마감 7일 전 알림 발송 시각. NULL이면 미발송 (v2.2.0 web push)';


-- ------------------------------------------------------------
-- local_places
-- ------------------------------------------------------------
CREATE TABLE local_places (
    id                BIGSERIAL    PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    category          VARCHAR(20)  NOT NULL,  -- '지원금사용처'|'농자재'|'농기계'|'농협'|'행정'|'생활'
    address           TEXT         NOT NULL,
    phone             VARCHAR(20)  NOT NULL DEFAULT '',
    lat               NUMERIC(10, 7) DEFAULT NULL,
    lng               NUMERIC(10, 7) DEFAULT NULL,
    subsidy_tags      TEXT[]       NOT NULL DEFAULT '{}',
    receipt_claimable BOOLEAN      NOT NULL DEFAULT FALSE,
    local_memo        TEXT         NOT NULL DEFAULT '',
    price_notes       TEXT         NOT NULL DEFAULT '',
    last_verified     DATE         DEFAULT NULL,
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  local_places                  IS '지역 내 지원금 사용 가능 장소 및 농업 관련 시설';
COMMENT ON COLUMN local_places.subsidy_tags      IS '지원금 종류 태그. 카카오 지도 필터에 사용';
COMMENT ON COLUMN local_places.receipt_claimable IS '영수증 청구 가능 여부';
COMMENT ON COLUMN local_places.lat               IS '위도 (카카오 로컬 API 지오코딩 결과)';
COMMENT ON COLUMN local_places.lng               IS '경도 (카카오 로컬 API 지오코딩 결과)';


-- ============================================================
-- INDEXES
-- ============================================================

-- policies — 1차 SQL 필터 성능
CREATE INDEX idx_policies_age         ON policies (min_age, max_age);
CREATE INDEX idx_policies_apply_end   ON policies (apply_end_date);
CREATE INDEX idx_policies_is_active   ON policies (is_active);

-- GIN — ArrayField overlap/contains 연산
CREATE INDEX idx_policies_region_codes    ON policies USING GIN (region_codes);
CREATE INDEX idx_policies_occupation_tags ON policies USING GIN (occupation_tags);
CREATE INDEX idx_policies_income_level    ON policies USING GIN (income_level);

-- GIN — JSONB condition_tree 조회 (optional)
CREATE INDEX idx_policies_condition_tree  ON policies USING GIN (condition_tree);

-- local_places
CREATE INDEX idx_places_category     ON local_places (category);
CREATE INDEX idx_places_subsidy_tags ON local_places USING GIN (subsidy_tags);

-- user_policies
CREATE INDEX idx_user_policies_profile ON user_policies (profile_id);
CREATE INDEX idx_user_policies_policy  ON user_policies (policy_id);
CREATE INDEX idx_user_policies_status  ON user_policies (status);


-- ============================================================
-- TRIGGERS — updated_at 자동 갱신
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_local_places_updated_at
    BEFORE UPDATE ON local_places
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
-- ENTITY RELATIONSHIP SUMMARY
--
--  regions (code PK)
--      ↑ (soft ref via region_code TEXT)
--  user_profiles
--      └── user_id  → users.id          (1:1, CASCADE)
--      └── id       ← user_policies.profile_id (1:N)
--
--  policies.id ← user_policies.policy_id (N:1)
--
--  Relationships:
--    users         1──1  user_profiles
--    user_profiles 1──N  user_policies
--    policies      1──N  user_policies
--    regions       (계층: parent_code → code, recursive CTE)
-- ============================================================
