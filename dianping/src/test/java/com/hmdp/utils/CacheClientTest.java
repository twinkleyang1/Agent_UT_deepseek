package com.hmdp.utils;

import cn.hutool.json.JSONUtil;
import com.hmdp.entity.Shop;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class CacheClientTest {

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    private CacheClient cacheClient;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
        cacheClient = new CacheClient(stringRedisTemplate);
    }

    @Test
    void shouldReturnCachedWhenQueryWithLogicalExpire() {
        // Arrange
        String keyPrefix = "cache:shop:";
        Long id = 1L;
        String key = keyPrefix + id;

        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Test Shop");

        RedisData redisData = new RedisData();
        redisData.setData(shop);
        redisData.setExpireTime(LocalDateTime.now().plusHours(1));

        String json = JSONUtil.toJsonStr(redisData);
        when(valueOps.get(key)).thenReturn(json);

        // Act
        Shop result = cacheClient.queryWithLogicalExpire(
                keyPrefix, id, Shop.class, null, 30L, TimeUnit.MINUTES);

        // Assert
        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("Test Shop", result.getName());
        verify(valueOps).get(key);
    }

    @Test
    void shouldReturnCachedWhenQueryWithPassThrough() {
        // Arrange
        String keyPrefix = "cache:shop:";
        Long id = 1L;
        String key = keyPrefix + id;

        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Test Shop");

        String json = JSONUtil.toJsonStr(shop);
        when(valueOps.get(key)).thenReturn(json);

        // Act
        Shop result = cacheClient.queryWithPassThrough(
                keyPrefix, id, Shop.class, null, 30L, TimeUnit.MINUTES);

        // Assert
        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("Test Shop", result.getName());
        verify(valueOps).get(key);
    }
}
