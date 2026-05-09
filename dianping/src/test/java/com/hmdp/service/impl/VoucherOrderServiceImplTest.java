package com.hmdp.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.hmdp.dto.Result;
import com.hmdp.entity.VoucherOrder;
import com.hmdp.mapper.VoucherOrderMapper;
import com.hmdp.service.ISeckillVoucherService;
import com.hmdp.utils.RedisIdWorker;
import com.hmdp.utils.UserHolder;
import com.hmdp.dto.UserDTO;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Answers;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherOrderServiceImplTest {

    @Mock private VoucherOrderMapper baseMapper;
    @Mock(answer = Answers.RETURNS_DEEP_STUBS)
    private ISeckillVoucherService seckillVoucherService;
    @Mock private RabbitTemplate rabbitTemplate;
    @Mock private RedisIdWorker redisIdWorker;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private RedissonClient redissonClient;
    @Mock private RLock lock;
    @InjectMocks private VoucherOrderServiceImpl service;

    @BeforeEach
    void setUp() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldSeckillVoucherSuccess() {
        when(redisIdWorker.nextId("order")).thenReturn(100L);
        when(stringRedisTemplate.execute(any(DefaultRedisScript.class), anyList(), anyString(), anyString(), anyString()))
                .thenReturn(0L);
        doNothing().when(rabbitTemplate).convertAndSend(anyString(), anyString(), anyString());

        Result result = service.seckillVoucher(10L);

        assertTrue(result.getSuccess());
        assertEquals(100L, result.getData());
        verify(rabbitTemplate).convertAndSend(eq("X"), eq("XA"), anyString());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldFailSeckillVoucherOutOfStock() {
        when(redisIdWorker.nextId("order")).thenReturn(100L);
        when(stringRedisTemplate.execute(any(DefaultRedisScript.class), anyList(), anyString(), anyString(), anyString()))
                .thenReturn(1L);

        Result result = service.seckillVoucher(10L);

        assertFalse(result.getSuccess());
        assertEquals("库存不足", result.getErrorMsg());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldFailSeckillVoucherDuplicate() {
        when(redisIdWorker.nextId("order")).thenReturn(100L);
        when(stringRedisTemplate.execute(any(DefaultRedisScript.class), anyList(), anyString(), anyString(), anyString()))
                .thenReturn(2L);

        Result result = service.seckillVoucher(10L);

        assertFalse(result.getSuccess());
        assertEquals("不能重复下单", result.getErrorMsg());
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldNotCreateVoucherOrderWhenAlreadyBought() {
        VoucherOrder order = new VoucherOrder();
        order.setUserId(1L);
        order.setVoucherId(10L);
        when(baseMapper.selectCount(any(Wrapper.class))).thenReturn(1);

        service.createVoucherOrder(order);

        verify(baseMapper, never()).insert(any());
    }
}
