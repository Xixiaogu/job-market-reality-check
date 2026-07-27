export default defineBackground(() => {
  console.log('Job Market Collector background started.', {
    id: browser.runtime.id,
  });
});
