package com.hmdp.service.impl;

import com.hmdp.entity.SeckillVoucher;
import com.hmdp.entity.Voucher;
import com.hmdp.mapper.VoucherMapper;
import com.hmdp.service.ISeckillVoucherService;
import com.hmdp.utils.RedisConstants;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.LocalDateTime;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherServiceImplTest {

    @Mock
    private VoucherMapper baseMapper;

    @Mock
    private ISeckillVoucherService seckillVoucherService;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @InjectMocks
    private VoucherServiceImpl voucherService;

    @Test
    void shouldAddSeckillVoucherSuccessfully() {
        // Arrange
        Voucher voucher = new Voucher();
        voucher.setId(1L);
        voucher.setStock(100);
        LocalDateTime now = LocalDateTime.now();
        voucher.setBeginTime(now);
        voucher.setEndTime(now.plusDays(1));

        when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);

        // Act
        voucherService.addSeckillVoucher(voucher);

        // Assert
        verify(baseMapper).insert(any(Voucher.class));
        verify(seckillVoucherService).save(any(SeckillVoucher.class));
        verify(stringRedisTemplate).opsForValue();
        verify(valueOps).set(eq(RedisConstants.SECKILL_STOCK_KEY + "1"), eq("100"));
    }
}
