package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.entity.Voucher;
import com.hmdp.entity.SeckillVoucher;
import com.hmdp.mapper.VoucherMapper;
import com.hmdp.service.ISeckillVoucherService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherServiceImplTest {

    @Mock private VoucherMapper baseMapper;
    @Mock private ISeckillVoucherService seckillVoucherService;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ValueOperations<String, String> valueOps;
    @InjectMocks private VoucherServiceImpl service;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
    }

    @Test
    void shouldReturnVouchersForShop() {
        Voucher v = new Voucher().setId(1L).setTitle("50% off");
        when(baseMapper.queryVoucherOfShop(10L)).thenReturn(List.of(v));

        Result result = service.queryVoucherOfShop(10L);

        assertTrue(result.getSuccess());
        assertEquals(1, ((List<?>) result.getData()).size());
    }

    @Test
    void shouldReturnEmptyListWhenNoVouchers() {
        when(baseMapper.queryVoucherOfShop(10L)).thenReturn(Collections.emptyList());

        Result result = service.queryVoucherOfShop(10L);

        assertTrue(result.getSuccess());
        assertTrue(((List<?>) result.getData()).isEmpty());
    }

    @Test
    void shouldAddSeckillVoucher() {
        Voucher v = new Voucher().setId(1L).setStock(100);
        when(baseMapper.insert(v)).thenReturn(1);
        when(seckillVoucherService.save(any(SeckillVoucher.class))).thenReturn(true);

        service.addSeckillVoucher(v);

        verify(baseMapper).insert(v);
        verify(seckillVoucherService).save(any(SeckillVoucher.class));
        verify(valueOps).set(contains("seckill:stock:1"), eq("100"));
    }
}
