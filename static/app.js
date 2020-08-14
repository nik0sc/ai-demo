"use strict";

(function () {
  function createFileInputHandler(i) {
    $(`#file-input-${i}`).change(function () {
      // append to img
      const reader = new FileReader();
      reader.onload = (e) => {
        $(`#image-${i}`).attr("src", e.target.result);
      };
      reader.readAsDataURL(this.files[0]);
      $(`#image-placeholder-${i}`).css("visibility", "hidden");
    });
  }

  $(() => {
    createFileInputHandler("1");
    createFileInputHandler("2");

    let result_valid = false;
    $("#submit").click(function () {
      const frame1 = $("#image-1").attr("src");
      const frame2 = $("#image-2").attr("src");
      // todo: check image sizes match (Or just leave that to the backend)
      this.disabled = true;
      $("#submit-message").text("");
      $.post(
        "/process",
        { frame1, frame2 },
        (data) => {
          result_valid = true;
          $("#result-container>").css("visibility", "hidden");
          $("#result-image-1").attr("src", frame1);
          $("#result-image-2")
            .attr("src", data.frameinter)
            .css("visibility", "visible");
          $("#result-image-3").attr("src", frame2);
          console.log(data.extra);
        },
        "json"
      )
        .fail((xhr) => {
          $("#submit-message").text(xhr.responseText);
        })
        .always(() => {
          this.disabled = false;
        });
    });

    let play_interval = null;
    $("#play").click(function () {
      if (play_interval === null && result_valid) {
        this.textContent = "Pause";
        let current_frame = 1;
        play_interval = setInterval(() => {
          if (current_frame > 3) {
            current_frame = 1;
          }
          $("#result-container>img").css("visibility", "hidden");
          $(`#result-image-${current_frame}`).css("visibility", "visible");
          current_frame++;
        }, 500);
      } else {
        this.textContent = "Play";
        clearInterval(play_interval);
        play_interval = null;
      }
    });
  });
})();
