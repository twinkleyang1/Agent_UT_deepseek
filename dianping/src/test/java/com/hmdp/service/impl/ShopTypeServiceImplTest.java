package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.entity.ShopType;
import com.hmdp.mapper.ShopTypeMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.ListOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ShopTypeServiceImplTest {

    @Mock private ShopTypeMapper baseMapper;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ListOperations<String, String> listOps;
    @InjectMocks private ShopTypeServiceImpl service;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForList()).thenReturn(listOps);
    }

    @Test
    void shouldReturnShopTypesFromRedisWhenCacheExists() {
        List<String> cached = List.of("{\"id\":1,\"name\":\"Food\"}", "{\"id\":2,\"name\":\"Drinks\"}");
        when(listOps.range(anyString(), eq(0L), eq(-1L))).thenReturn(cached);

        Result result = service.querySort();

        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        verify(baseMapper, never()).selectList(any());
    }

    @Test
    void shouldFallbackToDbWhenRedisEmpty() {
        when(listOps.range(anyString(), eq(0L), eq(-1L))).thenReturn(Collections.emptyList());
        ShopType st = new ShopType().setId(1L).setName("Food");
        when(baseMapper.selectList(any())).thenReturn(List.of(st));
        when(listOps.rightPush(anyString(), anyString())).thenReturn(1L);

        Result result = service.querySort();

        assertTrue(result.getSuccess());
        verify(baseMapper).selectList(any());
    }

    @Test
    void shouldFailWhenNoDataInRedisOrDb() {
        when(listOps.range(anyString(), eq(0L), eq(-1L))).thenReturn(Collections.emptyList());
        when(baseMapper.selectList(any())).thenReturn(Collections.emptyList());

        Result result = service.querySort();

        assertFalse(result.getSuccess());
        assertEquals("没有分类数据", result.getErrorMsg());
    }
}
