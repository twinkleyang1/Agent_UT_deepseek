package com.hmdp.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hmdp.dto.Result;
import com.hmdp.entity.Shop;
import com.hmdp.mapper.ShopMapper;
import com.hmdp.utils.CacheClient;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ShopServiceImplTest {

    @Mock
    private ShopMapper baseMapper;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private CacheClient clientClient;

    @InjectMocks
    private ShopServiceImpl shopService;

    @Test
    void shouldReturnResultWhenQueryShopByType() {
        // Arrange: no coordinates provided (x=null, y=null), should use DB query path
        Integer typeId = 1;
        Integer current = 1;

        Shop shop = new Shop();
        shop.setId(1L);
        shop.setName("Test Shop");
        shop.setTypeId(1L);

        Page<Shop> page = new Page<>(current, 5);
        page.setRecords(Collections.singletonList(shop));
        page.setTotal(1);

        when(baseMapper.selectPage(any(Page.class), any(Wrapper.class))).thenReturn(page);

        // Act
        Result result = shopService.queryShopByType(typeId, current, null, null);

        // Assert
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        @SuppressWarnings("unchecked")
        List<Shop> shops = (List<Shop>) result.getData();
        assertEquals(1, shops.size());
        assertEquals("Test Shop", shops.get(0).getName());
    }

    @Test
    void shouldReturnShopWhenQueryByIdExists() {
        // Arrange
        Long id = 1L;
        Shop shop = new Shop();
        shop.setId(id);
        shop.setName("Test Shop");

        when(clientClient.queryWithLogicalExpire(anyString(), eq(id), eq(Shop.class), any(), anyLong(), any()))
                .thenReturn(shop);

        // Act
        Result result = shopService.queryById(id);

        // Assert
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        assertEquals(shop, result.getData());
    }
}