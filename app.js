const API_BASE_URL = 'https://resume-api-resume-service-lxvnobexrq.cn-shanghai.fcapp.run/api';

let resumeId = null;
let selectedFile = null;

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('resumeFile');
const uploadBtn = document.getElementById('uploadBtn');
const resultSection = document.getElementById('resultSection');
const matchSection = document.getElementById('matchSection');
const matchBtn = document.getElementById('matchBtn');
const loading = document.getElementById('loading');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleFileSelect(files[0]);
    } else {
        alert('请上传 PDF 格式的文件');
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    if (file.size > 10 * 1024 * 1024) {
        alert('文件大小不能超过 10MB');
        return;
    }
    selectedFile = file;
    uploadBtn.disabled = false;
    uploadBtn.textContent = `已选择: ${file.name}`;
}

uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    showLoading(true);
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch(`${API_BASE_URL}/resume/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            resumeId = result.data.resume_id;
            await extractResumeInfo();
        } else {
            alert(result.error || '上传失败');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请检查后端服务是否启动');
    } finally {
        showLoading(false);
    }
});

async function extractResumeInfo() {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/resume/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ resume_id: resumeId })
        });

        const result = await response.json();

        if (result.success) {
            displayResumeInfo(result.data);
            resultSection.style.display = 'block';
            matchSection.style.display = 'block';
        } else {
            alert(result.error || '解析失败');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请检查后端服务是否启动');
    } finally {
        showLoading(false);
    }
}

function displayResumeInfo(data) {
    document.getElementById('name').textContent = data.name || '-';
    document.getElementById('phone').textContent = data.phone || '-';
    document.getElementById('email').textContent = data.email || '-';
    document.getElementById('address').textContent = data.address || '-';
    document.getElementById('jobIntent').textContent = data.job_intent || '-';
    document.getElementById('workYears').textContent = data.work_years || '-';
    document.getElementById('education').textContent = data.education || '-';
    document.getElementById('experience').textContent = data.experience || '-';

    const skillsContainer = document.getElementById('skills');
    skillsContainer.innerHTML = '';
    if (data.skills && data.skills.length > 0) {
        data.skills.forEach(skill => {
            const span = document.createElement('span');
            span.className = 'skill-tag';
            span.textContent = skill;
            skillsContainer.appendChild(span);
        });
    } else {
        skillsContainer.textContent = '-';
    }
}

matchBtn.addEventListener('click', async () => {
    const jobDesc = document.getElementById('jobDesc').value.trim();
    if (!jobDesc) {
        alert('请输入岗位描述');
        return;
    }
    if (!resumeId) {
        alert('请先上传简历');
        return;
    }

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/resume/match`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resume_id: resumeId,
                job_description: jobDesc
            })
        });

        const result = await response.json();

        if (result.success) {
            displayMatchResult(result.data);
        } else {
            alert(result.error || '匹配失败');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请检查后端服务是否启动');
    } finally {
        showLoading(false);
    }
});

function displayMatchResult(data) {
    const matchResult = document.getElementById('matchResult');
    matchResult.style.display = 'block';

    document.getElementById('matchScore').textContent = data.match_score || 0;

    const skillRate = Math.round((data.skill_match_rate || 0) * 100);
    document.getElementById('skillProgress').style.width = `${skillRate}%`;
    document.getElementById('skillRate').textContent = `${skillRate}%`;

    const expRate = Math.round((data.experience_relevance || 0) * 100);
    document.getElementById('expProgress').style.width = `${expRate}%`;
    document.getElementById('expRate').textContent = `${expRate}%`;

    const matchedSkillsContainer = document.getElementById('matchedSkills');
    matchedSkillsContainer.innerHTML = '';
    if (data.matched_skills && data.matched_skills.length > 0) {
        data.matched_skills.forEach(skill => {
            const span = document.createElement('span');
            span.className = 'skill-tag';
            span.textContent = skill;
            matchedSkillsContainer.appendChild(span);
        });
    } else {
        matchedSkillsContainer.textContent = '无';
    }

    const missingSkillsContainer = document.getElementById('missingSkills');
    missingSkillsContainer.innerHTML = '';
    if (data.missing_skills && data.missing_skills.length > 0) {
        data.missing_skills.forEach(skill => {
            const span = document.createElement('span');
            span.className = 'skill-tag';
            span.textContent = skill;
            missingSkillsContainer.appendChild(span);
        });
    } else {
        missingSkillsContainer.textContent = '无';
    }

    document.getElementById('analysis').textContent = data.analysis || '-';
}

function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}
