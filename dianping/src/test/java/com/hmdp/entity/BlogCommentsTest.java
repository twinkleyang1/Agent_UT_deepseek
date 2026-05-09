package com.hmdp.entity;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;

class BlogCommentsTest {

    @Test
    void shouldSetAndGetFields() {
        BlogComments bc = new BlogComments();
        bc.setId(1L);
        bc.setUserId(100L);
        bc.setBlogId(10L);
        bc.setParentId(0L);
        bc.setAnswerId(0L);
        bc.setContent("Great post!");
        bc.setLiked(5);
        bc.setStatus(true);
        LocalDateTime now = LocalDateTime.now();
        bc.setCreateTime(now);
        bc.setUpdateTime(now);

        assertEquals(1L, bc.getId());
        assertEquals(100L, bc.getUserId());
        assertEquals(10L, bc.getBlogId());
        assertEquals(0L, bc.getParentId());
        assertEquals(0L, bc.getAnswerId());
        assertEquals("Great post!", bc.getContent());
        assertEquals(5, bc.getLiked());
        assertTrue(bc.getStatus());
        assertEquals(now, bc.getCreateTime());
        assertEquals(now, bc.getUpdateTime());
    }

    @Test
    void shouldUseAccessorsChain() {
        BlogComments bc = new BlogComments()
                .setId(1L)
                .setUserId(100L)
                .setContent("Nice!");

        assertEquals(1L, bc.getId());
        assertEquals(100L, bc.getUserId());
        assertEquals("Nice!", bc.getContent());
    }
}
