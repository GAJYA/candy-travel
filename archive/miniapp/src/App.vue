<script setup lang="ts">
import { onHide, onLaunch, onShow } from "@dcloudio/uni-app";

onLaunch(() => {
  console.log("CandyTravel Mini Program Launch");
});

onShow(() => {
  console.log("CandyTravel Mini Program Show");
});

onHide(() => {
  console.log("CandyTravel Mini Program Hide");
});
</script>

<style lang="scss">
page {
  background: #fff7fb;
  color: #1f2937;
  font-family: "PingFang SC", "Helvetica Neue", sans-serif;
}

view,
text,
button,
input,
textarea,
navigator {
  box-sizing: border-box;
}
</style>
