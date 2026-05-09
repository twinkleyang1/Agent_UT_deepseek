package com.hmdp.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.Blog;
import com.hmdp.entity.User;
import com.hmdp.mapper.BlogMapper;
import com.hmdp.service.IFollowService;
import com.hmdp.service.IUserService;
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
import org.springframework.data.redis.core.ZSetOperations;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BlogServiceImplTest {

    @Mock private BlogMapper baseMapper;
    @Mock private IUserService userService;
    @Mock private IFollowService followService;
    @Mock private StringRedisTemplate stringRedisTemplate;
    @Mock private ZSetOperations<String, String> zSetOps;
    @InjectMocks private BlogServiceImpl service;

    @BeforeEach
    void setUp() {
        UserDTO user = new UserDTO();
        user.setId(1L);
        UserHolder.saveUser(user);
        when(stringRedisTemplate.opsForZSet()).thenReturn(zSetOps);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    @SuppressWarnings("unchecked")
    void shouldQueryHotBlog() {
        Blog blog = new Blog();
        blog.setId(1L);
        blog.setUserId(2L);
        when(baseMapper.selectPage(any(Page.class), any(Wrapper.class))).thenReturn(
                new Page<Blog>(1, 10).setRecords(List.of(blog)));
        when(zSetOps.score(anyString(), anyString())).thenReturn(null);
        User user = new User();
        user.setNickName("test");
        user.setIcon("icon.png");
        when(userService.getById(2L)).thenReturn(user);

        Result result = service.queryHotBlog(1);

        assertTrue(result.getSuccess());
        List<Blog> blogs = (List<Blog>) result.getData();
        assertEquals(1, blogs.size());
    }

    @Test
    void shouldLikeWhenNotLiked() {
        when(zSetOps.score(anyString(), eq("1"))).thenReturn(null);
        when(baseMapper.update(isNull(), any(Wrapper.class))).thenReturn(1);
        when(zSetOps.add(anyString(), eq("1"), anyDouble())).thenReturn(true);

        Result result = service.updateLike(10L);

        assertTrue(result.getSuccess());
        verify(zSetOps).add(anyString(), eq("1"), anyDouble());
    }

    @Test
    void shouldUnlikeWhenAlreadyLiked() {
        when(zSetOps.score(anyString(), eq("1"))).thenReturn(1.0);
        when(baseMapper.update(isNull(), any(Wrapper.class))).thenReturn(1);
        when(zSetOps.remove(anyString(), eq("1"))).thenReturn(1L);

        Result result = service.updateLike(10L);

        assertTrue(result.getSuccess());
        verify(zSetOps).remove(anyString(), eq("1"));
    }

    @Test
    void shouldReturnEmptyWhenNoLikes() {
        when(zSetOps.range(anyString(), eq(0L), eq(4L))).thenReturn(Collections.emptySet());

        Result result = service.queryBlogLikes(10L);

        assertTrue(result.getSuccess());
        assertEquals(Collections.emptyList(), result.getData());
    }

    @Test
    void shouldReturnEmptyWhenNullLikes() {
        when(zSetOps.range(anyString(), eq(0L), eq(4L))).thenReturn(null);

        Result result = service.queryBlogLikes(10L);

        assertTrue(result.getSuccess());
        assertEquals(Collections.emptyList(), result.getData());
    }

    @Test
    void shouldFailSaveWhenInsertFails() {
        Blog blog = new Blog();
        when(baseMapper.insert(blog)).thenReturn(0);

        Result result = service.saveBlog(blog);

        assertFalse(result.getSuccess());
        assertEquals("新增笔记失败", result.getErrorMsg());
    }

    @Test
    void shouldQueryBlogByIdFound() {
        Blog blog = new Blog();
        blog.setId(1L);
        blog.setUserId(2L);
        when(baseMapper.selectById(1L)).thenReturn(blog);
        when(zSetOps.score(anyString(), eq("1"))).thenReturn(null);
        User user = new User();
        user.setNickName("test");
        user.setIcon("icon.png");
        when(userService.getById(2L)).thenReturn(user);

        Result result = service.queryBlogById(1L);

        assertTrue(result.getSuccess());
        Blog data = (Blog) result.getData();
        assertEquals(1L, data.getId());
    }

    @Test
    void shouldFailQueryBlogByIdNotFound() {
        when(baseMapper.selectById(99L)).thenReturn(null);

        Result result = service.queryBlogById(99L);

        assertFalse(result.getSuccess());
        assertEquals("博客不存在", result.getErrorMsg());
    }

    @Test
    void shouldReturnEmptyQuertBlogOfFollowWhenNoFeeds() {
        when(zSetOps.reverseRangeByScoreWithScores(anyString(), anyDouble(), anyDouble(), anyLong(), anyInt()))
                .thenReturn(null);

        Result result = service.quertBlogOfFollow(100L, 0);

        assertTrue(result.getSuccess());
        assertNull(result.getData());
    }
}
