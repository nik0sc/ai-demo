"use strict";

(function () {
  const files_uploaded = {};
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

  function extraButtonActive(button) {
    $("#extra-control-container button")
      .addClass("btn-outline-primary")
      .removeClass("btn-primary");
    $(button).addClass("btn-primary").removeClass("btn-outline-primary");
  }

  $(() => {
    createFileInputHandler("1");
    createFileInputHandler("2");

    let result_valid = false;
    $("#submit").click(function () {
      const frame1 = $("#image-1")[0].src;
      const frame2 = $("#image-2")[0].src;
      const t = $("#param-t")[0].value;
      const downsample = $("#param-downsample")[0].checked;
      const outformat = $("#param-outformat")[0].value;
      // todo: check image sizes match (Or just leave that to the backend)
      this.disabled = true;
      $("#submit-message").text("").addClass("d-none");
      $("#spinner").removeClass("d-none");
      $.post(
        "/process",
        { frame1, frame2, t, downsample, outformat },
        (data) => {
          result_valid = true;
          $("#result-container>").css("visibility", "hidden");
          $("#result-image-1").attr("src", frame1);
          $("#result-image-2")
            .attr("src", data.frameinter)
            .css("visibility", "visible");
          $("#result-image-3").attr("src", frame2);
          $("#result-control-container button").attr("disabled", false);
          $("#result-flow-1").attr("src", data.extra.flow_t_0);
          $("#result-flow-2").attr("src", data.extra.flow_t_1);
          $("#result-wm-1").attr("src", data.extra.w1);
          $("#result-wm-2").attr("src", data.extra.w2);
        },
        "json"
      )
        .fail((xhr) => {
          $("#submit-message").text(xhr.responseText).removeClass("d-none");
        })
        .always(() => {
          this.disabled = false;
          $("#spinner").addClass("d-none");
        });
    });

    let play_interval = null;
    $("#play").click(function () {
      if (play_interval === null && result_valid) {
        this.textContent = "Pause";
        $("#extra-control-container button").attr("disabled", true);
        $("#result-container .--extra").css("visibility", "hidden");
        $("#extra-control-container button")
          .addClass("btn-outline-primary")
          .removeClass("btn-primary");
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
        $("#extra-control-container button").attr("disabled", false);
        clearInterval(play_interval);
        play_interval = null;
      }
    });

    $("#show-flow-1").click(function () {
      extraButtonActive(this);
      $("#result-container img").css("visibility", "hidden");
      $("#result-image-1").css("visibility", "visible");
      $("#result-flow-1").css("visibility", "visible");
    });

    $("#show-flow-2").click(function () {
      extraButtonActive(this);
      $("#result-container img").css("visibility", "hidden");
      $("#result-image-3").css("visibility", "visible");
      $("#result-flow-2").css("visibility", "visible");
    });

    $("#show-wm-1").click(function () {
      extraButtonActive(this);
      $("#result-container img").css("visibility", "hidden");
      $("#result-image-1").css("visibility", "visible");
      $("#result-wm-1").css("visibility", "visible");
    });

    $("#show-wm-2").click(function () {
      extraButtonActive(this);
      $("#result-container img").css("visibility", "hidden");
      $("#result-image-3").css("visibility", "visible");
      $("#result-wm-2").css("visibility", "visible");
    });
  });
})();
