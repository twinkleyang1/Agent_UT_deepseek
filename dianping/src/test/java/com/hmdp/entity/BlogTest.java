package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class BlogTest {

    @Test
    void shouldSetAndGetId() {
        Blog blog = new Blog();
        blog.setId(1L);
        assertEquals(1L, blog.getId());
    }

    @Test
    void shouldSetAndGetShopId() {
        Blog blog = new Blog();
        blog.setShopId(10L);
        assertEquals(10L, blog.getShopId());
    }

    @Test
    void shouldSetAndGetUserId() {
        Blog blog = new Blog();
        blog.setUserId(100L);
        assertEquals(100L, blog.getUserId());
    }

    @Test
    void shouldSetAndGetIcon() {
        Blog blog = new Blog();
        blog.setIcon("user-icon.png");
        assertEquals("user-icon.png", blog.getIcon());
    }

    @Test
    void shouldSetAndGetName() {
        Blog blog = new Blog();
        blog.setName("Alice");
        assertEquals("Alice", blog.getName());
    }

    @Test
    void shouldSetAndGetIsLike() {
        Blog blog = new Blog();
        blog.setIsLike(true);
        assertTrue(blog.getIsLike());

        blog.setIsLike(false);
        assertFalse(blog.getIsLike());
    }

    @Test
    void shouldSetAndGetTitle() {
        Blog blog = new Blog();
        blog.setTitle("My Blog Title");
        assertEquals("My Blog Title", blog.getTitle());
    }

    @Test
    void shouldSetAndGetImages() {
        Blog blog = new Blog();
        blog.setImages("img1.jpg,img2.jpg");
        assertEquals("img1.jpg,img2.jpg", blog.getImages());
    }

    @Test
    void shouldSetAndGetContent() {
        Blog blog = new Blog();
        blog.setContent("Blog content here");
        assertEquals("Blog content here", blog.getContent());
    }

    @Test
    void shouldSetAndGetLikedAndComments() {
        Blog blog = new Blog();
        blog.setLiked(42);
        blog.setComments(10);

        assertEquals(42, blog.getLiked());
        assertEquals(10, blog.getComments());
    }

    @Test
    void shouldSetAndGetTimestamps() {
        Blog blog = new Blog();
        LocalDateTime now = LocalDateTime.now();
        blog.setCreateTime(now);
        blog.setUpdateTime(now);

        assertEquals(now, blog.getCreateTime());
        assertEquals(now, blog.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        Blog blog = new Blog()
                .setId(1L)
                .setShopId(10L)
                .setTitle("Test");

        assertEquals(1L, blog.getId());
        assertEquals(10L, blog.getShopId());
        assertEquals("Test", blog.getTitle());
    }
}
