document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  
  e.preventDefault();
    
  const formData = new FormData(e.target);
  const file = formData.get('file');
  const task = formData.get('task');
  const resultDiv = document.getElementById('result');
  const loader = document.createElement('div');
  
  // Reset UI (KHÔNG reset preview)
  resultDiv.innerHTML = '';
  loader.className = 'loader';
  resultDiv.appendChild(loader);
  loader.style.display = 'block';

  try {
      const response = await fetch('http://localhost:3000/upload', { 
          method: 'POST',
          body: formData,
          headers: {
              // 
          }
      });

      // Xử lý response chi tiết 
      if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: "Unknown server error" }));
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Kiểm tra dữ liệu hợp lệ 
      if (!data) throw new Error("Empty response from server");
      
      loader.style.display = 'none';

      // Hiển thị kết quả
      if (data.result_path) {
        const img = document.createElement('img');
        img.src = `${data.result_path}?t=${Date.now()}`; // Cache busting
        img.alt = 'Processed Image';
        img.style.maxWidth = '100%';
        img.onerror = () => {
            resultDiv.innerHTML = `<p style="color: red;">Lỗi tải ảnh kết quả</p>`;
        };
        resultDiv.appendChild(img);
          
      } else if (data.age !== undefined) {
          const translations = {
              age: 'Tuổi',
              gender: 'Giới tính',
              emotion: 'Cảm xúc nổi bật'
          };

          const emotionTranslations = {
            'angry': 'Tức giận',
            'disgust': 'Khó chịu',
            'fear': 'Sợ hãi',
            'happy': 'Vui vẻ',
            'sad': 'Buồn',
            'surprise': 'Ngạc nhiên',
            'neutral': 'Bình thường'
          };

          const translatedData = {
            age: data.age,
            gender: data.gender === 'Man' ? 'Nam' : 'Nữ',  // Dịch sang tiếng Việt
            emotion: emotionTranslations[data.emotion] || data.emotion
          };

          const resultHtml = `
              <div class="result-box">
                  <h3>Kết quả phân tích</h3>
                  <ul>
                      ${Object.entries(translatedData)
                          .map(([key, value]) => `
                              <li><strong>${translations[key] || key}:</strong> ${value}</li>
                          `).join('')}
                  </ul>
              </div>
          `;
          resultDiv.innerHTML = resultHtml;
          
      } else {
          throw new Error("Invalid response format");
      }

  } catch (error) {
      console.error('Error:', error);
      loader.style.display = 'none';
      resultDiv.innerHTML = `
          <p style="color: red;">
              Lỗi: ${error.message || 'Không thể kết nối đến server'}
              ${error.message.includes('Failed to fetch') ? '<br>(Kiểm tra server có đang chạy không)' : ''}
          </p>
      `;
  }
});

//Thêm validation cho file ảnh
document.querySelector('input[type="file"]').addEventListener('change', function(e) {
  const file = e.target.files[0];
  const previewImg = document.getElementById('preview');
  const resultDiv = document.getElementById('result');
  
  resultDiv.innerHTML = '';
  previewImg.src = '#';

  if (!file) return;

  // Kiểm tra định dạng file
  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!validTypes.includes(file.type)) {
      e.target.value = ''; // Reset input
      alert('Chỉ chấp nhận file ảnh (JPEG/PNG/WEBP)');
      return;
  }

  // Kiểm tra kích thước file (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
      e.target.value = '';
      alert('File quá lớn! Kích thước tối đa: 5MB');
      return;
  }

  // Hiển thị preview
  const reader = new FileReader();
  reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewImg.style.display = 'block';
  };
  reader.onerror = () => {
      alert('Lỗi đọc file');
      e.target.value = '';
  };
  reader.readAsDataURL(file);
  
});

