package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.mapper.VoucherOrderMapper;
import com.hmdp.service.ISeckillVoucherService;
import com.hmdp.utils.RedisIdWorker;
import com.hmdp.utils.UserHolder;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.redisson.api.RedissonClient;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VoucherOrderServiceImplTest {

    @Mock
    private VoucherOrderMapper baseMapper;

    @Mock
    private ISeckillVoucherService seckillVoucherService;

    @Mock
    private RabbitTemplate rabbitTemplate;

    @Mock
    private RedisIdWorker redisIdWorker;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private RedissonClient redissonClient;

    @InjectMocks
    private VoucherOrderServiceImpl service;

    private UserDTO testUser;

    @BeforeEach
    void setUp() {
        testUser = new UserDTO();
        testUser.setId(1L);
        testUser.setNickName("testUser");
        UserHolder.saveUser(testUser);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldReturnResultWhenSeckillVoucher() {
        // Arrange: lua script returns 0 (success), MQ send succeeds
        Long voucherId = 100L;
        Long expectedOrderId = 20240001L;

        when(redisIdWorker.nextId("order")).thenReturn(expectedOrderId);
        when(stringRedisTemplate.execute(
                any(DefaultRedisScript.class),
                anyList(),
                anyString(), anyString(), anyString()
        )).thenReturn(0L);
        doNothing().when(rabbitTemplate).convertAndSend(anyString(), anyString(), anyString());

        // Act
        Result result = service.seckillVoucher(voucherId);

        // Assert
        assertTrue(result.getSuccess());
        assertEquals(expectedOrderId, result.getData());

        verify(redisIdWorker).nextId("order");
        verify(stringRedisTemplate).execute(
                any(DefaultRedisScript.class),
                anyList(),
                eq(voucherId.toString()),
                eq(testUser.getId().toString()),
                eq(expectedOrderId.toString())
        );
        verify(rabbitTemplate).convertAndSend(eq("X"), eq("XA"), anyString());
    }
}
