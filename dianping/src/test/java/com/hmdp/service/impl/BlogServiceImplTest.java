package com.hmdp.service.impl;

import com.hmdp.dto.Result;
import com.hmdp.dto.ScrollResult;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.Blog;
import com.hmdp.entity.User;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hmdp.mapper.BlogMapper;
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
import org.springframework.data.redis.core.DefaultTypedTuple;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BlogServiceImplTest {

    @Mock
    private BlogMapper blogMapper;

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Mock
    private ZSetOperations<String, String> zSetOps;

    @Mock
    private IUserService userService;

    @InjectMocks
    private BlogServiceImpl blogService;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForZSet()).thenReturn(zSetOps);
    }

    @AfterEach
    void tearDown() {
        UserHolder.removeUser();
    }

    @Test
    void shouldReturnResultWhenQuertBlogOfFollow() {
        // Arrange - set current user via UserHolder
        UserDTO userDTO = new UserDTO();
        userDTO.setId(1L);
        UserHolder.saveUser(userDTO);

        // Mock Redis ZSet reverseRangeByScoreWithScores: return 2 blog entries
        Set<ZSetOperations.TypedTuple<String>> tuples = new LinkedHashSet<>();
        tuples.add(new DefaultTypedTuple<>("10", 1000.0));
        tuples.add(new DefaultTypedTuple<>("20", 1000.0));
        when(zSetOps.reverseRangeByScoreWithScores(anyString(), anyDouble(), anyDouble(), anyLong(), anyLong()))
                .thenReturn(tuples);

        // Mock zSetOps.score for isBlogLiked (return non-null = liked)
        when(zSetOps.score(anyString(), anyString())).thenReturn(1.0);

        // Mock baseMapper.selectList for chain call query().in().last().list()
        Blog blog1 = new Blog();
        blog1.setId(10L);
        blog1.setUserId(2L);
        Blog blog2 = new Blog();
        blog2.setId(20L);
        blog2.setUserId(3L);
        when(blogMapper.selectList(any())).thenReturn(Arrays.asList(blog1, blog2));

        // Mock userService.getById for queryBlogUser
        User user1 = new User();
        user1.setNickName("Alice");
        user1.setIcon("icon1.png");
        User user2 = new User();
        user2.setNickName("Bob");
        user2.setIcon("icon2.png");
        when(userService.getById(2L)).thenReturn(user1);
        when(userService.getById(3L)).thenReturn(user2);

        // Act
        Result result = blogService.quertBlogOfFollow(Long.MAX_VALUE, 0);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        ScrollResult scrollResult = (ScrollResult) result.getData();
        assertNotNull(scrollResult);
        List<?> blogs = scrollResult.getList();
        assertEquals(2, blogs.size());
        assertEquals(1000L, scrollResult.getMinTime().longValue());
        assertEquals(2, scrollResult.getOffset().intValue());

        // Verify blog was enriched with user info and like status
        Blog resultBlog1 = (Blog) blogs.get(0);
        assertEquals("Alice", resultBlog1.getName());
        assertEquals("icon1.png", resultBlog1.getIcon());
        assertTrue(resultBlog1.getIsLike());

        Blog resultBlog2 = (Blog) blogs.get(1);
        assertEquals("Bob", resultBlog2.getName());
        assertEquals("icon2.png", resultBlog2.getIcon());
        assertTrue(resultBlog2.getIsLike());
    }

    @Test
    void shouldReturnResultWhenQueryHotBlog() {
        // Arrange - set current user via UserHolder so isBlogLiked does not short-circuit
        UserDTO userDTO = new UserDTO();
        userDTO.setId(1L);
        UserHolder.saveUser(userDTO);

        // Mock baseMapper.selectPage for query().orderByDesc("liked").page()
        Blog blog1 = new Blog();
        blog1.setId(10L);
        blog1.setUserId(2L);
        Blog blog2 = new Blog();
        blog2.setId(20L);
        blog2.setUserId(3L);

        when(blogMapper.selectPage(any(), any())).thenAnswer(invocation -> {
            Page<Blog> page = invocation.getArgument(0);
            page.setRecords(Arrays.asList(blog1, blog2));
            page.setTotal(2);
            return page;
        });

        // Mock zSetOps.score for isBlogLiked (return non-null = liked)
        when(zSetOps.score(anyString(), anyString())).thenReturn(1.0);

        // Mock userService.getById for queryBlogUser
        User user1 = new User();
        user1.setNickName("Alice");
        user1.setIcon("icon1.png");
        User user2 = new User();
        user2.setNickName("Bob");
        user2.setIcon("icon2.png");
        when(userService.getById(2L)).thenReturn(user1);
        when(userService.getById(3L)).thenReturn(user2);

        // Act
        Result result = blogService.queryHotBlog(1);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        List<?> records = (List<?>) result.getData();
        assertNotNull(records);
        assertEquals(2, records.size());

        Blog resultBlog1 = (Blog) records.get(0);
        assertEquals("Alice", resultBlog1.getName());
        assertEquals("icon1.png", resultBlog1.getIcon());
        assertTrue(resultBlog1.getIsLike());

        Blog resultBlog2 = (Blog) records.get(1);
        assertEquals("Bob", resultBlog2.getName());
        assertEquals("icon2.png", resultBlog2.getIcon());
        assertTrue(resultBlog2.getIsLike());
    }

    @Test
    void shouldReturnResultWhenUpdateLike() {
        // Arrange - set current user via UserHolder
        UserDTO userDTO = new UserDTO();
        userDTO.setId(1L);
        UserHolder.saveUser(userDTO);

        Long blogId = 10L;
        String keyPrefix = "blog:liked:";

        // User hasn't liked this blog yet → zset score returns null
        when(zSetOps.score(contains(keyPrefix), eq("1"))).thenReturn(null);

        // MyBatis-Plus chain: update().setSql("liked=liked+1").eq("id", id).update()
        // internally calls baseMapper.update(null, UpdateWrapper)
        // Return 1 to indicate 1 row affected → isSuccess = true
        when(blogMapper.update(isNull(), any())).thenReturn(1);

        // Act
        Result result = blogService.updateLike(blogId);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());

        // Verify DB update was called (like count +1)
        verify(blogMapper).update(isNull(), any());

        // Verify Redis ZSet add was called (user added to liked set)
        verify(zSetOps).add(contains(keyPrefix), eq("1"), anyDouble());
    }
}
