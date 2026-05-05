<template>
  <view class="candy-icon" :class="`candy-icon--${safeName}`">
    <view class="candy-icon__part candy-icon__part--a" />
    <view class="candy-icon__part candy-icon__part--b" />
    <view class="candy-icon__part candy-icon__part--c" />
    <view class="candy-icon__part candy-icon__part--d" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
}>()

const safeName = computed(() => props.name.replace(/[^a-z0-9-]/gi, '') || 'pin')
</script>

<style lang="scss">
.candy-icon {
  position: relative;
  width: 1em;
  height: 1em;
  color: currentColor;
}
.candy-icon__part {
  position: absolute;
  box-sizing: border-box;
  border-color: currentColor;
}

.candy-icon--home .candy-icon__part--a {
  left: 18%;
  top: 42%;
  width: 64%;
  height: 42%;
  border: 0.12em solid currentColor;
  border-top: 0;
  border-radius: 0 0 0.12em 0.12em;
}
.candy-icon--home .candy-icon__part--b {
  left: 24%;
  top: 15%;
  width: 52%;
  height: 52%;
  border-left: 0.12em solid currentColor;
  border-top: 0.12em solid currentColor;
  border-radius: 0.08em;
  transform: rotate(45deg);
}

.candy-icon--calendar .candy-icon__part--a {
  left: 14%;
  top: 18%;
  width: 72%;
  height: 68%;
  border: 0.11em solid currentColor;
  border-radius: 0.14em;
}
.candy-icon--calendar .candy-icon__part--b {
  left: 20%;
  right: 20%;
  top: 42%;
  height: 0.1em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--calendar .candy-icon__part--c,
.candy-icon--calendar .candy-icon__part--d {
  top: 8%;
  width: 0.1em;
  height: 0.22em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--calendar .candy-icon__part--c {
  left: 32%;
}
.candy-icon--calendar .candy-icon__part--d {
  right: 32%;
}

.candy-icon--ai .candy-icon__part--a,
.candy-icon--sparkle .candy-icon__part--a {
  left: 44%;
  top: 10%;
  width: 0.12em;
  height: 0.76em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--ai .candy-icon__part--b,
.candy-icon--sparkle .candy-icon__part--b {
  left: 12%;
  top: 42%;
  width: 0.76em;
  height: 0.12em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--ai .candy-icon__part--c,
.candy-icon--sparkle .candy-icon__part--c {
  right: 4%;
  top: 4%;
  width: 0.18em;
  height: 0.18em;
  border-radius: 50%;
  background: currentColor;
}
.candy-icon--ai .candy-icon__part--d,
.candy-icon--sparkle .candy-icon__part--d {
  left: 5%;
  bottom: 6%;
  width: 0.14em;
  height: 0.14em;
  border-radius: 50%;
  background: currentColor;
}

.candy-icon--user .candy-icon__part--a {
  left: 34%;
  top: 12%;
  width: 32%;
  height: 32%;
  border-radius: 50%;
  background: currentColor;
}
.candy-icon--user .candy-icon__part--b {
  left: 20%;
  bottom: 12%;
  width: 60%;
  height: 34%;
  border-radius: 0.36em 0.36em 0.14em 0.14em;
  background: currentColor;
}

.candy-icon--pin .candy-icon__part--a {
  left: 27%;
  top: 8%;
  width: 46%;
  height: 52%;
  border: 0.12em solid currentColor;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
}
.candy-icon--pin .candy-icon__part--b {
  left: 43%;
  top: 24%;
  width: 14%;
  height: 14%;
  border-radius: 50%;
  background: currentColor;
}

.candy-icon--plane .candy-icon__part--a {
  left: 12%;
  top: 45%;
  width: 78%;
  height: 0.12em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(-12deg);
}
.candy-icon--plane .candy-icon__part--b {
  left: 40%;
  top: 21%;
  width: 0.12em;
  height: 0.44em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(-47deg);
}
.candy-icon--plane .candy-icon__part--c {
  left: 44%;
  top: 45%;
  width: 0.12em;
  height: 0.34em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(55deg);
}
.candy-icon--plane .candy-icon__part--d {
  left: 18%;
  top: 35%;
  width: 0.16em;
  height: 0.26em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(-12deg);
}

.candy-icon--train .candy-icon__part--a,
.candy-icon--bus .candy-icon__part--a {
  left: 16%;
  top: 16%;
  width: 68%;
  height: 58%;
  border: 0.11em solid currentColor;
  border-radius: 0.16em;
}
.candy-icon--train .candy-icon__part--b,
.candy-icon--bus .candy-icon__part--b {
  left: 26%;
  right: 26%;
  top: 36%;
  height: 0.1em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--train .candy-icon__part--c,
.candy-icon--bus .candy-icon__part--c,
.candy-icon--train .candy-icon__part--d,
.candy-icon--bus .candy-icon__part--d {
  bottom: 10%;
  width: 0.14em;
  height: 0.14em;
  border-radius: 50%;
  background: currentColor;
}
.candy-icon--train .candy-icon__part--c,
.candy-icon--bus .candy-icon__part--c {
  left: 28%;
}
.candy-icon--train .candy-icon__part--d,
.candy-icon--bus .candy-icon__part--d {
  right: 28%;
}

.candy-icon--car .candy-icon__part--a {
  left: 18%;
  top: 42%;
  width: 64%;
  height: 28%;
  border: 0.11em solid currentColor;
  border-radius: 0.14em;
}
.candy-icon--car .candy-icon__part--b {
  left: 30%;
  top: 24%;
  width: 40%;
  height: 28%;
  border: 0.11em solid currentColor;
  border-bottom: 0;
  border-radius: 0.18em 0.18em 0 0;
}
.candy-icon--car .candy-icon__part--c,
.candy-icon--car .candy-icon__part--d {
  bottom: 12%;
  width: 0.16em;
  height: 0.16em;
  border-radius: 50%;
  background: currentColor;
}
.candy-icon--car .candy-icon__part--c {
  left: 28%;
}
.candy-icon--car .candy-icon__part--d {
  right: 28%;
}

.candy-icon--hotel .candy-icon__part--a {
  left: 22%;
  top: 14%;
  width: 56%;
  height: 72%;
  border: 0.11em solid currentColor;
  border-radius: 0.1em;
}
.candy-icon--hotel .candy-icon__part--b {
  left: 43%;
  bottom: 14%;
  width: 14%;
  height: 24%;
  border-radius: 0.08em 0.08em 0 0;
  background: currentColor;
}
.candy-icon--hotel .candy-icon__part--c,
.candy-icon--hotel .candy-icon__part--d {
  top: 30%;
  width: 0.12em;
  height: 0.12em;
  border-radius: 0.04em;
  background: currentColor;
}
.candy-icon--hotel .candy-icon__part--c {
  left: 34%;
}
.candy-icon--hotel .candy-icon__part--d {
  right: 34%;
}

.candy-icon--ship .candy-icon__part--a {
  left: 14%;
  top: 50%;
  width: 72%;
  height: 24%;
  border-bottom: 0.13em solid currentColor;
  border-left: 0.13em solid currentColor;
  border-radius: 0 0 0.34em 0.34em;
  transform: skewX(-18deg);
}
.candy-icon--ship .candy-icon__part--b {
  left: 46%;
  top: 14%;
  height: 42%;
  width: 0.12em;
  background: currentColor;
}
.candy-icon--ship .candy-icon__part--c {
  left: 48%;
  top: 18%;
  width: 28%;
  height: 24%;
  border: 0.1em solid currentColor;
  border-left: 0;
}
.candy-icon--ship .candy-icon__part--d {
  left: 18%;
  right: 18%;
  bottom: 4%;
  height: 0.1em;
  border-radius: 1em;
  background: currentColor;
  opacity: 0.5;
}

.candy-icon--food .candy-icon__part--a {
  left: 26%;
  top: 14%;
  width: 0.1em;
  height: 72%;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--food .candy-icon__part--b {
  left: 16%;
  top: 14%;
  width: 0.3em;
  height: 0.3em;
  border-top: 0.1em solid currentColor;
  border-left: 0.1em solid currentColor;
  border-right: 0.1em solid currentColor;
}
.candy-icon--food .candy-icon__part--c {
  right: 26%;
  top: 14%;
  width: 0.11em;
  height: 72%;
  border-radius: 1em 1em 0 0;
  background: currentColor;
}

.candy-icon--coffee .candy-icon__part--a {
  left: 18%;
  top: 40%;
  width: 54%;
  height: 34%;
  border: 0.11em solid currentColor;
  border-radius: 0.08em 0.08em 0.24em 0.24em;
}
.candy-icon--coffee .candy-icon__part--b {
  right: 12%;
  top: 46%;
  width: 20%;
  height: 20%;
  border: 0.1em solid currentColor;
  border-left: 0;
  border-radius: 0 0.2em 0.2em 0;
}
.candy-icon--coffee .candy-icon__part--c,
.candy-icon--coffee .candy-icon__part--d {
  top: 12%;
  width: 0.08em;
  height: 0.22em;
  border-radius: 1em;
  background: currentColor;
  opacity: 0.7;
}
.candy-icon--coffee .candy-icon__part--c {
  left: 34%;
}
.candy-icon--coffee .candy-icon__part--d {
  left: 52%;
}

.candy-icon--museum .candy-icon__part--a {
  left: 16%;
  top: 18%;
  width: 68%;
  height: 0;
  border-left: 0.34em solid transparent;
  border-right: 0.34em solid transparent;
  border-bottom: 0.18em solid currentColor;
}
.candy-icon--museum .candy-icon__part--b {
  left: 18%;
  right: 18%;
  bottom: 14%;
  height: 0.1em;
  background: currentColor;
}
.candy-icon--museum .candy-icon__part--c,
.candy-icon--museum .candy-icon__part--d {
  top: 42%;
  width: 0.1em;
  height: 32%;
  background: currentColor;
}
.candy-icon--museum .candy-icon__part--c {
  left: 34%;
}
.candy-icon--museum .candy-icon__part--d {
  right: 34%;
}

.candy-icon--park .candy-icon__part--a,
.candy-icon--spa .candy-icon__part--a {
  left: 24%;
  top: 20%;
  width: 48%;
  height: 36%;
  border-radius: 50% 0 50% 50%;
  border: 0.11em solid currentColor;
  transform: rotate(-35deg);
}
.candy-icon--park .candy-icon__part--b,
.candy-icon--spa .candy-icon__part--b {
  left: 48%;
  top: 48%;
  width: 0.1em;
  height: 36%;
  border-radius: 1em;
  background: currentColor;
}

.candy-icon--shopping .candy-icon__part--a {
  left: 22%;
  top: 34%;
  width: 56%;
  height: 48%;
  border: 0.11em solid currentColor;
  border-radius: 0.1em;
}
.candy-icon--shopping .candy-icon__part--b {
  left: 34%;
  top: 18%;
  width: 32%;
  height: 28%;
  border: 0.1em solid currentColor;
  border-bottom: 0;
  border-radius: 0.2em 0.2em 0 0;
}

.candy-icon--ticket .candy-icon__part--a {
  left: 16%;
  top: 28%;
  width: 68%;
  height: 44%;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}
.candy-icon--ticket .candy-icon__part--b {
  left: 47%;
  top: 34%;
  width: 0.08em;
  height: 32%;
  border-radius: 1em;
  background: currentColor;
  opacity: 0.6;
}

.candy-icon--camera .candy-icon__part--a {
  left: 16%;
  top: 32%;
  width: 68%;
  height: 44%;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}
.candy-icon--camera .candy-icon__part--b {
  left: 39%;
  top: 42%;
  width: 22%;
  height: 22%;
  border: 0.1em solid currentColor;
  border-radius: 50%;
}
.candy-icon--camera .candy-icon__part--c {
  left: 28%;
  top: 24%;
  width: 24%;
  height: 12%;
  border-radius: 0.08em 0.08em 0 0;
  background: currentColor;
}

.candy-icon--luggage .candy-icon__part--a {
  left: 24%;
  top: 26%;
  width: 52%;
  height: 58%;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}
.candy-icon--luggage .candy-icon__part--b {
  left: 38%;
  top: 14%;
  width: 24%;
  height: 18%;
  border: 0.1em solid currentColor;
  border-bottom: 0;
  border-radius: 0.12em 0.12em 0 0;
}

.candy-icon--clock .candy-icon__part--a {
  left: 16%;
  top: 16%;
  width: 68%;
  height: 68%;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}
.candy-icon--clock .candy-icon__part--b {
  left: 48%;
  top: 28%;
  width: 0.09em;
  height: 28%;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--clock .candy-icon__part--c {
  left: 48%;
  top: 50%;
  width: 24%;
  height: 0.09em;
  border-radius: 1em;
  background: currentColor;
}

.candy-icon--check .candy-icon__part--a {
  left: 20%;
  top: 46%;
  width: 28%;
  height: 0.13em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(45deg);
}
.candy-icon--check .candy-icon__part--b {
  left: 38%;
  top: 38%;
  width: 46%;
  height: 0.13em;
  border-radius: 1em;
  background: currentColor;
  transform: rotate(-45deg);
}

.candy-icon--note .candy-icon__part--a {
  left: 18%;
  top: 12%;
  width: 64%;
  height: 76%;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}
.candy-icon--note .candy-icon__part--b,
.candy-icon--note .candy-icon__part--c,
.candy-icon--note .candy-icon__part--d {
  left: 32%;
  width: 38%;
  height: 0.08em;
  border-radius: 1em;
  background: currentColor;
}
.candy-icon--note .candy-icon__part--b {
  top: 34%;
}
.candy-icon--note .candy-icon__part--c {
  top: 50%;
}
.candy-icon--note .candy-icon__part--d {
  top: 66%;
}
</style>
