package com.hmdp.utils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.core.script.DefaultRedisScript;

import java.util.Collections;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class SimpleRedisLockTest {

    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ValueOperations<String, String> valueOps;
    private SimpleRedisLock lock;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        lock = new SimpleRedisLock("test_lock", stringRedisTemplate);
    }

    @Test
    void shouldTryLockSuccess() {
        when(valueOps.setIfAbsent(contains("locktest_lock"), anyString(), eq(10L), eq(TimeUnit.SECONDS)))
                .thenReturn(true);

        boolean result = lock.tryLock(10L);

        assertTrue(result);
        verify(valueOps).setIfAbsent(contains("locktest_lock"), anyString(), eq(10L), eq(TimeUnit.SECONDS));
    }

    @Test
    void shouldTryLockFail() {
        when(valueOps.setIfAbsent(contains("locktest_lock"), anyString(), eq(5L), eq(TimeUnit.SECONDS)))
                .thenReturn(false);

        boolean result = lock.tryLock(5L);

        assertFalse(result);
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldDelLock() {
        when(stringRedisTemplate.execute(any(DefaultRedisScript.class), anyList(), anyString()))
                .thenReturn(1L);

        lock.delLock();

        verify(stringRedisTemplate).execute(any(DefaultRedisScript.class), eq(Collections.singletonList("locktest_lock")), anyString());
    }
}
