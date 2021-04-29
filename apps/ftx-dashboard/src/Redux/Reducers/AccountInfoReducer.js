import _ from 'lodash';

const SET_ACCOUNT_INFO = '@Redux/AccountInfo/SET_ACCOUNT_INFO';

const DEFAULT_STATE = {
  info: {},
};

export default function AccountInfoReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_ACCOUNT_INFO) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setAccountInfo(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (typeof obj.data.all === 'object') {
      payload.info = obj.data.all;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_ACCOUNT_INFO, payload };
}
