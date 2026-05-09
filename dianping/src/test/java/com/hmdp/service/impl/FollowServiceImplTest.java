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
import org.springframework.data.redis.core.SetOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class FollowServiceImplTest {

    @Mock private FollowMapper baseMapper;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private UserServiceImpl userService;
    @Mock private SetOperations<String, String> setOps;
    @InjectMocks private FollowServiceImpl service;

    @BeforeEach
    void setUp() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);
        when(stringRedisTemplate.opsForSet()).thenReturn(setOps);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldFollowWhenIsFollowTrue() {
        when(baseMapper.insert(any(Follow.class))).thenReturn(1);
        when(setOps.add(anyString(), anyString())).thenReturn(1L);

        Result result = service.follow(2L, true);

        assertTrue(result.getSuccess());
        verify(baseMapper).insert(any(Follow.class));
        verify(setOps).add(anyString(), eq("2"));
    }

    @Test
    void shouldUnfollowWhenIsFollowFalse() {
        when(baseMapper.delete(any())).thenReturn(1);
        when(setOps.remove(anyString(), any())).thenReturn(1L);

        Result result = service.follow(2L, false);

        assertTrue(result.getSuccess());
        verify(baseMapper).delete(any());
        verify(setOps).remove(anyString(), eq("2"));
    }

    @Test
    void shouldReturnTrueWhenIsFollowing() {
        when(baseMapper.selectCount(any())).thenReturn(1);

        Result result = service.isFollow(2L);

        assertTrue(result.getSuccess());
        assertTrue((Boolean) result.getData());
    }

    @Test
    void shouldReturnFalseWhenNotFollowing() {
        when(baseMapper.selectCount(any())).thenReturn(0);

        Result result = service.isFollow(2L);

        assertTrue(result.getSuccess());
        assertFalse((Boolean) result.getData());
    }

    @Test
    void shouldReturnCommonFollows() {
        Set<String> intersect = new HashSet<>();
        intersect.add("3");
        when(setOps.intersect(anyString(), anyString())).thenReturn(intersect);
        when(userService.listByIds(anyList())).thenReturn(java.util.Collections.emptyList());

        Result result = service.followCommons(5L);

        assertTrue(result.getSuccess());
        verify(setOps).intersect("follows:1", "follows:5");
    }
}
