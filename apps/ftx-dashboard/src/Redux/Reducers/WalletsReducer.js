import _ from 'lodash';

const SET_WALLETS = '@Redux/Wallets/SET_WALLETS';

const DEFAULT_STATE = {
  wallets: [],
  latestUpdate: new Date().toUTCString(),
};

export default function WalletsReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_WALLETS) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setWallets(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (Array.isArray(obj.data)) {
      payload.wallets = obj.data;
    }
    if (typeof obj.date === 'string') {
      payload.latestUpdate = obj.date;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_WALLETS, payload };
}
