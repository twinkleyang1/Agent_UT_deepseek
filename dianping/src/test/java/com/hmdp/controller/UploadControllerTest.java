package com.hmdp.controller;

import com.hmdp.dto.Result;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

import java.io.File;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.spy;

@ExtendWith(MockitoExtension.class)
class UploadControllerTest {

    @Test
    void shouldReturnResultWhenUploadImage() throws Exception {
        // Arrange
        UploadController controller = new UploadController();
        MockMultipartFile image = spy(new MockMultipartFile(
            "file", "test.jpg", "image/jpeg", "test content".getBytes()
        ));
        doNothing().when(image).transferTo(any(File.class));

        // Act
        Result result = controller.uploadImage(image);

        // Assert
        assertNotNull(result);
        assertTrue(result.getSuccess());
        assertNotNull(result.getData());
        assertTrue(result.getData().toString().contains("/blogs/"));
    }
}
