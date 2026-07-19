import pytest

from app.services.verification_service import VerificationError, VerificationService


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    def incr(self, key):
        self.commands.append(("incr", key, None))
        return self

    def expire(self, key, seconds, nx=False):
        self.commands.append(("expire", key, seconds))
        return self

    def set(self, key, value, ex=None):
        self.commands.append(("set", key, (value, ex)))
        return self

    def delete(self, key):
        self.commands.append(("delete", key, None))
        return self

    def execute(self):
        results = []
        for operation, key, value in self.commands:
            if operation == "incr":
                self.redis.values[key] = int(self.redis.values.get(key, 0)) + 1
                results.append(self.redis.values[key])
            elif operation == "expire":
                self.redis.expirations.setdefault(key, value)
                results.append(True)
            elif operation == "set":
                stored, seconds = value
                self.redis.values[key] = stored
                self.redis.expirations[key] = seconds
                results.append(True)
            else:
                results.append(bool(self.redis.values.pop(key, None)))
        return results


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        self.expirations[key] = ex
        return True

    def ttl(self, key):
        return self.expirations.get(key, -1)

    def pipeline(self):
        return FakePipeline(self)

    def delete(self, *keys):
        return sum(bool(self.values.pop(key, None)) for key in keys)

    def eval(self, script, key_count, code_key, attempts_key, supplied, ttl, max_attempts):
        stored = self.values.get(code_key)
        if stored is None:
            return -1
        if attempts_key in self.values and int(self.values[attempts_key]) >= int(max_attempts):
            return -2
        if stored == supplied:
            self.delete(code_key, attempts_key)
            return 1
        self.values[attempts_key] = int(self.values.get(attempts_key, 0)) + 1
        self.expirations[attempts_key] = int(ttl)
        if self.values[attempts_key] >= int(max_attempts):
            self.delete(code_key)
        return 0


class FakeEmailService:
    def __init__(self):
        self.messages = []

    def send_verification_code(self, recipient, code):
        self.messages.append((recipient, code))


def test_code_is_rate_limited_and_single_use():
    redis = FakeRedis()
    mailer = FakeEmailService()
    service = VerificationService(redis, mailer)

    result = service.send_code(" User@Example.com ", "register", "127.0.0.1")
    assert result.retry_after == 60
    assert len(mailer.messages) == 1

    with pytest.raises(VerificationError, match="发送过于频繁"):
        service.send_code("user@example.com", "register", "127.0.0.1")

    code = mailer.messages[0][1]
    service.verify("user@example.com", "register", code)
    with pytest.raises(VerificationError, match="已过期"):
        service.verify("user@example.com", "register", code)


def test_code_is_locked_after_five_wrong_attempts():
    redis = FakeRedis()
    mailer = FakeEmailService()
    service = VerificationService(redis, mailer)
    service.send_code("user@example.com", "register", "127.0.0.2")
    real_code = mailer.messages[0][1]
    wrong_code = "111111" if real_code == "000000" else "000000"

    for _ in range(4):
        with pytest.raises(VerificationError, match="不正确"):
            service.verify("user@example.com", "register", wrong_code)
    with pytest.raises(VerificationError, match="不正确"):
        service.verify("user@example.com", "register", wrong_code)

    with pytest.raises(VerificationError, match="已过期"):
        service.verify("user@example.com", "register", real_code)
