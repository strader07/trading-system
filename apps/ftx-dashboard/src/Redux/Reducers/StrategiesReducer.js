import _ from 'lodash';

const SET_STRATEGIES = '@Redux/Strategies/SET_STRATEGIES';

const DEFAULT_STATE = {
  strategies: [],
  latestUpdate: new Date().toUTCString(),
};

export default function StrategiesReducer(state = DEFAULT_STATE, action) {
  if (action.type === SET_STRATEGIES) {
    return _.assign({}, state, action.payload);
  } else {
    return state;
  }
}

export function setStrategies(str) {
  let payload = DEFAULT_STATE;
  try {
    const obj = JSON.parse(str || '{}');
    if (Array.isArray(obj.data.breakdown)) {
      payload.strategies = obj.data.breakdown;
    }
    if (typeof obj.date === 'string') {
      payload.latestUpdate = obj.date;
    }
  } catch (err) {
    console.error(err);
  }
  return { type: SET_STRATEGIES, payload };
}
