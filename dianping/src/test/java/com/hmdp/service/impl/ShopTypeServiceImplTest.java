package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.entity.ShopType;
import com.hmdp.mapper.ShopTypeMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.ListOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ShopTypeServiceImplTest {

    @Mock
    private ShopTypeMapper baseMapper;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ListOperations<String, String> listOps;

    @InjectMocks
    private ShopTypeServiceImpl shopTypeService;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForList()).thenReturn(listOps);
    }

    @AfterEach
    void tearDown() {
        reset(baseMapper, stringRedisTemplate, listOps);
    }

    @Test
    void shouldReturnResultWhenQuerySort() {
        // Arrange: cache miss - Redis returns null
        when(listOps.range("shop_type:", 0, -1)).thenReturn(null);

        // DB returns shop types
        ShopType type1 = new ShopType().setId(1L).setName("美食").setSort(1);
        ShopType type2 = new ShopType().setId(2L).setName("娱乐").setSort(2);
        List<ShopType> shopTypes = Arrays.asList(type1, type2);

        when(baseMapper.selectList(any(com.baomidou.mybatisplus.core.conditions.Wrapper.class)))
                .thenReturn(shopTypes);

        // Act
        Result result = shopTypeService.querySort();

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());

        // Verify Redis was populated
        verify(listOps, times(2)).rightPush(eq("shop_type:"), anyString());
    }
}
