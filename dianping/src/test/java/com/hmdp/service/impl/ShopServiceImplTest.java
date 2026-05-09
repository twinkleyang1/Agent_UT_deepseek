package com.hmdp.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hmdp.dto.Result;
import com.hmdp.entity.Shop;
import com.hmdp.mapper.ShopMapper;
import com.hmdp.utils.CacheClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.geo.*;
import org.springframework.data.redis.connection.RedisGeoCommands;
import org.springframework.data.redis.core.GeoOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.domain.geo.GeoReference;

import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ShopServiceImplTest {

    @Mock private ShopMapper baseMapper;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private CacheClient cacheClient;
    @Mock private ValueOperations<String, String> valueOps;
    @Mock private GeoOperations<String, String> geoOps;
    @InjectMocks private ShopServiceImpl service;

    @Test
    void shouldQueryByIdSuccess() {
        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Test Shop");
        when(cacheClient.queryWithLogicalExpire(anyString(), eq(1L), eq(Shop.class), any(), anyLong(), any(TimeUnit.class)))
                .thenReturn(shop);

        Result result = service.queryById(1L);

        assertTrue(result.getSuccess());
        assertEquals(shop, result.getData());
    }

    @Test
    void shouldQueryByIdNotFound() {
        when(cacheClient.queryWithLogicalExpire(anyString(), eq(99L), eq(Shop.class), any(), anyLong(), any(TimeUnit.class)))
                .thenReturn(null);

        Result result = service.queryById(99L);

        assertFalse(result.getSuccess());
        assertEquals("店铺不存在！", result.getErrorMsg());
    }

    @Test
    void shouldUpdateShop() {
        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Updated");
        when(baseMapper.updateById(shop)).thenReturn(1);
        when(stringRedisTemplate.delete(contains("cache:shop:"))).thenReturn(true);

        Result result = service.update(shop);

        assertTrue(result.getSuccess());
        verify(baseMapper).updateById(shop);
        verify(stringRedisTemplate).delete(contains("cache:shop:"));
    }

    @Test
    void shouldFailUpdateWhenIdNull() {
        Shop shop = new Shop();

        Result result = service.update(shop);

        assertFalse(result.getSuccess());
        assertEquals("店铺id不能为空", result.getErrorMsg());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldQueryShopByTypeWithoutCoords() {
        Shop shop = new Shop();
        shop.setId(1L);
        shop.setTypeId(5L);
        when(baseMapper.selectPage(any(Page.class), any(Wrapper.class))).thenReturn(
                new Page<Shop>(1, 10).setRecords(List.of(shop)));

        Result result = service.queryShopByType(5, 1, null, null);

        assertTrue(result.getSuccess());
        List<Shop> shops = (List<Shop>) result.getData();
        assertEquals(1, shops.size());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldQueryShopByTypeWithCoords() {
        when(stringRedisTemplate.opsForGeo()).thenReturn(geoOps);
        GeoResult<RedisGeoCommands.GeoLocation<String>> geoResult =
                new GeoResult<>(new RedisGeoCommands.GeoLocation<>("1", new Point(1, 1)), new Distance(1));
        GeoResults<RedisGeoCommands.GeoLocation<String>> geoResults =
                new GeoResults<>(List.of(geoResult));
        when(geoOps.search(anyString(), any(GeoReference.class), any(Distance.class), any(RedisGeoCommands.GeoSearchCommandArgs.class)))
                .thenReturn(geoResults);
        Shop shop = new Shop();
        shop.setId(1L);
        when(baseMapper.selectList(any(Wrapper.class))).thenReturn(List.of(shop));

        Result result = service.queryShopByType(5, 1, 1.0, 1.0);

        assertTrue(result.getSuccess());
        List<Shop> shops = (List<Shop>) result.getData();
        assertEquals(1, shops.size());
    }

    @Test
    void shouldReturnEmptyWhenGeoResultsNull() {
        when(stringRedisTemplate.opsForGeo()).thenReturn(geoOps);
        when(geoOps.search(anyString(), any(GeoReference.class), any(Distance.class), any(RedisGeoCommands.GeoSearchCommandArgs.class)))
                .thenReturn(null);

        Result result = service.queryShopByType(5, 1, 1.0, 1.0);

        assertTrue(result.getSuccess());
        assertEquals(Collections.emptyList(), result.getData());
    }
}
