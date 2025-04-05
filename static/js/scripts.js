// 初始化视频播放器
document.addEventListener('DOMContentLoaded', function() {
    const videoModal = document.getElementById('videoModal');

    videoModal.addEventListener('hidden.bs.modal', function () {
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.pause();
        videoPlayer.currentTime = 0;
    });
});

// 处理视频播放结束
document.getElementById('videoPlayer').addEventListener('ended', function() {
    $('#videoModal').modal('hide');
});