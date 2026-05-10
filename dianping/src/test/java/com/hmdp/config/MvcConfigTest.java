package com.hmdp.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;

import java.lang.reflect.Field;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class MvcConfigTest {

    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @Test
    void shouldAddInterceptorsSuccessfully() throws Exception {
        // Arrange
        MvcConfig mvcConfig = new MvcConfig();
        Field field = MvcConfig.class.getDeclaredField("stringRedisTemplate");
        field.setAccessible(true);
        field.set(mvcConfig, stringRedisTemplate);

        InterceptorRegistry registry = new InterceptorRegistry();

        // Act
        mvcConfig.addInterceptors(registry);

        // Assert - getInterceptors() is protected, use reflection
        java.lang.reflect.Method method = InterceptorRegistry.class.getDeclaredMethod("getInterceptors");
        method.setAccessible(true);
        @SuppressWarnings("unchecked")
        List<Object> interceptors = (List<Object>) method.invoke(registry);
        assertNotNull(interceptors);
        assertEquals(2, interceptors.size());
    }
}
