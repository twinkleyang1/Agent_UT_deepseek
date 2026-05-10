package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.Follow;
import com.hmdp.mapper.FollowMapper;
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
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.SetOperations;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class FollowServiceImplTest {

    @Mock
    private FollowMapper baseMapper;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private SetOperations<String, String> setOps;

    @InjectMocks
    private FollowServiceImpl followService;

    private UserDTO testUser;

    @BeforeEach
    void setUp() {
        testUser = new UserDTO();
        testUser.setId(1L);
        testUser.setNickName("testUser");
        UserHolder.saveUser(testUser);

        when(stringRedisTemplate.opsForSet()).thenReturn(setOps);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldReturnResultWhenFollow() {
        // Arrange
        Long followUserId = 2L;
        Boolean isFollow = true;

        when(baseMapper.insert(any(Follow.class))).thenReturn(1);

        // Act
        Result result = followService.follow(followUserId, isFollow);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        verify(baseMapper, times(1)).insert(any(Follow.class));
        verify(setOps, times(1)).add("follows:1", "2");
    }
}
