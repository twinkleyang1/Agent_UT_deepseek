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

import java.util.concurrent.TimeUnit;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class CacheClientTest {

    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ValueOperations<String, String> valueOps;
    @InjectMocks private CacheClient cacheClient;

    @Test
    void shouldSet() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);

        cacheClient.set("key1", "value1", 10L, TimeUnit.MINUTES);

        verify(valueOps).set(eq("key1"), anyString(), eq(10L), eq(TimeUnit.MINUTES));
    }

    @Test
    void shouldSetWithLogicalExpire() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);

        cacheClient.setWithLogicalExpire("key1", "value1", 10L, TimeUnit.MINUTES);

        verify(valueOps).set(eq("key1"), anyString());
    }
}
