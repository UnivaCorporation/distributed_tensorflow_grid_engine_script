require 'spec_helper'
describe 'tortuga_tensorflow' do
  context 'with default values for all parameters' do
    it { should contain_class('tortuga_tensorflow') }
  end
end
