# config/settings.py 에 추가할 DRF 설정
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS':    'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER':       'config.exception_handler.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# 로깅 — Railway에서 stdout으로 바로 확인 가능
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{levelname}] {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
