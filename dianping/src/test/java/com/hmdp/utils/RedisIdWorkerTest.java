package com.hmdp.utils;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class RedisIdWorkerTest {

    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ValueOperations<String, String> valueOps;
    @InjectMocks private RedisIdWorker redisIdWorker;

    @Test
    void shouldReturnNextId() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment(contains("icr:order:"))).thenReturn(1L);

        Long id = redisIdWorker.nextId("order");

        assertNotNull(id);
        assertTrue(id > 0);
        verify(valueOps).increment(contains("icr:order:"));
    }

    @Test
    void shouldReturnDifferentIdsForDifferentKeys() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment(contains("icr:order:"))).thenReturn(1L);
        when(valueOps.increment(contains("icr:voucher:"))).thenReturn(5L);

        Long id1 = redisIdWorker.nextId("order");
        Long id2 = redisIdWorker.nextId("voucher");

        assertNotNull(id1);
        assertNotNull(id2);
        verify(valueOps).increment(contains("icr:order:"));
        verify(valueOps).increment(contains("icr:voucher:"));
    }
}
