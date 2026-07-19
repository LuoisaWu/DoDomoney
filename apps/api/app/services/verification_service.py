import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass

try:
    from redis import Redis
    from redis.exceptions import RedisError
except ImportError:  # Allows unrelated commands to run before requirements are installed.
    Redis = None  # type: ignore[assignment,misc]

    class RedisError(Exception):
        pass

from app.core.config import settings
from app.services.email_service import EmailService


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class VerificationError(ValueError):
    pass


class VerificationUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class SendResult:
    retry_after: int
    expires_in: int
    development_code: str | None = None


VERIFY_SCRIPT = """
local stored = redis.call('GET', KEYS[1])
if not stored then return -1 end
local previous_attempts = tonumber(redis.call('GET', KEYS[2]) or '0')
if previous_attempts >= tonumber(ARGV[3]) then return -2 end
if stored == ARGV[1] then
  redis.call('DEL', KEYS[1], KEYS[2])
  return 1
end
local attempts = redis.call('INCR', KEYS[2])
if attempts == 1 then redis.call('EXPIRE', KEYS[2], ARGV[2]) end
if attempts >= tonumber(ARGV[3]) then redis.call('DEL', KEYS[1]) end
return 0
"""


class VerificationService:
    def __init__(self, redis_client: object | None = None, email_service: EmailService | None = None) -> None:
        self.redis = redis_client or (Redis.from_url(settings.redis_url, decode_responses=True) if Redis else None)
        self.email_service = email_service or EmailService()

    @staticmethod
    def normalize_email(email: str) -> str:
        normalized = email.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise VerificationError("请输入有效的邮箱地址")
        return normalized

    def _identity(self, email: str) -> str:
        return hmac.new(
            settings.verification_code_secret.encode(), email.encode(), hashlib.sha256
        ).hexdigest()

    def _digest(self, email: str, purpose: str, code: str) -> str:
        payload = f"{email}:{purpose}:{code}".encode()
        return hmac.new(settings.verification_code_secret.encode(), payload, hashlib.sha256).hexdigest()

    def _keys(self, email: str, purpose: str) -> tuple[str, str, str]:
        identity = self._identity(email)
        prefix = f"dodomoney:verify:{purpose}:{identity}"
        return f"{prefix}:code", f"{prefix}:attempts", f"{prefix}:cooldown"

    def send_code(self, email: str, purpose: str, client_ip: str) -> SendResult:
        if self.redis is None:
            raise VerificationUnavailableError("验证码服务暂时不可用，请先安装 Redis 客户端")
        normalized = self.normalize_email(email)
        code_key, attempts_key, cooldown_key = self._keys(normalized, purpose)
        ip_identity = self._identity(client_ip or "unknown")
        ip_limit_key = f"dodomoney:verify:ip:{ip_identity}:hour"
        email_limit_key = f"dodomoney:verify:email:{self._identity(normalized)}:day"

        try:
            if not self.redis.set(
                cooldown_key, "1", nx=True, ex=settings.verification_send_cooldown_seconds
            ):
                retry_after = max(int(self.redis.ttl(cooldown_key)), 1)
                raise VerificationError(f"发送过于频繁，请在 {retry_after} 秒后重试")

            pipe = self.redis.pipeline()
            pipe.incr(ip_limit_key)
            pipe.expire(ip_limit_key, 3600, nx=True)
            pipe.incr(email_limit_key)
            pipe.expire(email_limit_key, 86400, nx=True)
            ip_count, _, email_count, _ = pipe.execute()
            if int(ip_count) > 10 or int(email_count) > 20:
                self.redis.delete(cooldown_key)
                raise VerificationError("验证码请求次数过多，请稍后再试")

            code = f"{secrets.randbelow(1_000_000):06d}"
            pipe = self.redis.pipeline()
            pipe.set(code_key, self._digest(normalized, purpose, code), ex=settings.verification_code_ttl_seconds)
            pipe.delete(attempts_key)
            pipe.execute()
            try:
                self.email_service.send_verification_code(normalized, code)
            except Exception:
                self.redis.delete(code_key, attempts_key, cooldown_key)
                raise
        except VerificationError:
            raise
        except (RedisError, OSError, RuntimeError) as exc:
            raise VerificationUnavailableError("验证码服务暂时不可用，请稍后再试") from exc

        development_code = None
        if settings.environment == "development" and settings.expose_verification_code:
            development_code = code
        return SendResult(
            retry_after=settings.verification_send_cooldown_seconds,
            expires_in=settings.verification_code_ttl_seconds,
            development_code=development_code,
        )

    def verify(self, email: str, purpose: str, code: str) -> None:
        if self.redis is None:
            raise VerificationUnavailableError("验证码服务暂时不可用，请先安装 Redis 客户端")
        normalized = self.normalize_email(email)
        code_key, attempts_key, _ = self._keys(normalized, purpose)
        try:
            result = int(self.redis.eval(
                VERIFY_SCRIPT,
                2,
                code_key,
                attempts_key,
                self._digest(normalized, purpose, code),
                settings.verification_code_ttl_seconds,
                settings.verification_max_attempts,
            ))
        except RedisError as exc:
            raise VerificationUnavailableError("验证码服务暂时不可用，请稍后再试") from exc

        if result == 1:
            return
        if result == -1:
            raise VerificationError("验证码已过期，请重新获取")
        if result == -2:
            raise VerificationError("验证码尝试次数过多，请重新获取")
        raise VerificationError("验证码不正确")
