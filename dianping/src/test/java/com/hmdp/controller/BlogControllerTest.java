package com.hmdp.controller;

import com.hmdp.dto.Result;
import com.hmdp.dto.UserDTO;
import com.hmdp.entity.Blog;
import com.hmdp.service.IBlogService;
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

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BlogControllerTest {

    @Mock private IBlogService blogService;
    @Mock private com.hmdp.service.IUserService userService;
    @InjectMocks private BlogController controller;

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
    void shouldSaveBlog() {
        Blog blog = new Blog();
        blog.setTitle("test");
        when(blogService.saveBlog(blog)).thenReturn(Result.ok(1L));

        Result result = controller.saveBlog(blog);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldLikeBlog() {
        when(blogService.updateLike(10L)).thenReturn(Result.ok());

        Result result = controller.likeBlog(10L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryHotBlog() {
        when(blogService.queryHotBlog(1)).thenReturn(Result.ok());

        Result result = controller.queryHotBlog(1);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryBlogById() {
        when(blogService.queryBlogById(1L)).thenReturn(Result.ok());

        Result result = controller.queryById(1L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryBlogLikes() {
        when(blogService.queryBlogLikes(1L)).thenReturn(Result.ok());

        Result result = controller.queryBlogLikes(1L);

        assertTrue(result.getSuccess());
    }

    @Test
    void shouldQueryBlogOfFollow() {
        when(blogService.quertBlogOfFollow(100L, 0)).thenReturn(Result.ok());

        Result result = controller.queryBlogOfFollow(100L, 0);

        assertTrue(result.getSuccess());
    }
}
