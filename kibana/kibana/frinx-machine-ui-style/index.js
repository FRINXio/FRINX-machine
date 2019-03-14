
export default function (kibana) {
  return new kibana.Plugin({
   uiExports: {
     app: {
        title: 'Frinx Machine UI Style',
        order: -100,
        description: 'Frinx Machine UI Style',
        main: 'plugins/frinx-machine-ui-style/index.js',
        hidden: true
     }
    }
  });
};
