package com.hmdp.utils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RedisIdWorkerTest {

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @InjectMocks
    private RedisIdWorker redisIdWorker;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
    }

    @Test
    void shouldReturnLongWhenNextId() {
        // Arrange
        String keyPrefix = "order";
        long count = 88L;
        when(valueOps.increment(argThat(key -> key != null && key.startsWith("icr:" + keyPrefix + ":"))))
                .thenReturn(count);

        // Act
        Long result = redisIdWorker.nextId(keyPrefix);

        // Assert
        assertNotNull(result);
        assertTrue(result > 0);
        // The lower 32 bits should match the count returned by increment
        assertEquals(count, result & 0xFFFFFFFFL);

        verify(valueOps).increment(argThat(key -> key != null && key.startsWith("icr:" + keyPrefix + ":")));
    }
}
